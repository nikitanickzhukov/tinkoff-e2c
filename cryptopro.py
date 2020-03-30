import os
import subprocess
import tempfile
import base64
import re

import logging
logger = logging.getLogger(__name__)


class CryptoProError(Exception):
    code = None
    def __init__(self, message, code=-1):
        super().__init__(message)
        self.code = code

    def __str__(self):
        return '%d: %s' % (self.code, super().__str__())


class CryptoPro():
    """
    A class for getting hashes, signatures and certificate numbers
    for secure connection client's system with Tinkoff bank's E2C

    Methods
    -------
    get_hash()
        get content's hashsum
    get_sign()
        get content's signature
    get_containers()
        get containers which are set up
    get_certificates()
        get certificates which are set up on `store_name`
    get_certificate_serial()
        get serial number of certificate which is associated with `container_name`
    to_base64()
        convert binary content to base64 encoding
    """

    prefix = '/opt/cprocsp/bin/amd64/'
    encoding = 'utf-8'

    def __init__(self, container_name=None, store_name=None, encryption_provider=80, sign_algorithm='GOST12_256'):
        """
        Parameters
        ----------
        container_name[str]: a name of container to use as an encryptor (like '\\\\.\\HDIMAGE\\xxx...')
        store_name[str]: a name of store where certificate is located (like 'uMy')
        encryption_provider[int]: an encryption provider (like 75, 80, ...)
        sign_algorithm[str]: an algorithm to use when generating a hash or a signature (like 'GOST12_256', 'GOST12_512', ...)
        """

        self.container_name = container_name
        self.store_name = store_name
        self.encryption_provider = encryption_provider
        self.sign_algorithm = sign_algorithm

    def get_hash(self, content):
        """
        Returns generated hash of certain content

        Parameters
        ----------
        content[str, bytes]: a content to be hashed

        Returns
        -------
        bytes: a result hash

        Raises
        ------
        CryptoProError: when got an encryption error
        OSError: when got OS filesystem error
        """

        for k in ('sign_algorithm', 'container_name', 'encryption_provider'):
            assert getattr(self, k), '%s must be defined' % (k,)

        in_file_name = self._create_temp_file(content)
        out_file_name = in_file_name + '.hash'

        res = self._execute(
            "csptest",
            "-keyset",
            "-hash", "%(sign_algorithm)s",
            "-silent",
            "-cont", "%(container_name)s",
            "-keytype", "exchange",
            "-in", "%(in_file)s",
            "-hashout", "%(out_file)s",
            "-provtype", "%(encryption_provider)d",
            in_file=in_file_name,
            out_file=out_file_name
        )

        self._flush_temp_file(in_file_name)

        if res.returncode:
            raise self._get_error(res)

        result = self._flush_temp_file(out_file_name)

        return result

    def get_sign(self, content):
        """
        Returns generated signature of certain content

        Parameters
        ----------
        content[str, bytes]: a content to be signed

        Returns
        -------
        bytes: a result signature

        Raises
        ------
        CryptoProError: when got an encryption error
        OSError: when got OS filesystem error
        """

        for k in ('sign_algorithm', 'container_name', 'encryption_provider'):
            assert getattr(self, k), '%s must be defined' % (k,)

        in_file_name = self._create_temp_file(content)
        out_file_name = in_file_name + '.sign'

        res = self._execute(
            "csptest",
            "-keyset",
            "-sign", "%(sign_algorithm)s",
            "-silent",
            "-cont", "%(container_name)s",
            "-keytype", "exchange",
            "-in", "%(in_file)s",
            "-out", "%(out_file)s",
            "-provtype", "%(encryption_provider)d",
            in_file=in_file_name,
            out_file=out_file_name
        )

        self._flush_temp_file(in_file_name)

        if res.returncode:
            raise self._get_error(res)

        result = self._flush_temp_file(out_file_name)

        return result

    def get_containers(self):
        """
        Returns a list of available containers

        Returns
        -------
        list: containers

        Raises
        ------
        CryptoProError: when got an encryption error
        OSError: when got OS filesystem error
        """

        result = self._execute(
            "csptest",
            "-keyset",
            "-enum_cont",
            "-fqcn",
            "-verifyc",
            "-uniq"
        )

        lines = self._get_lines(result.stdout)
        items = []

        for line in lines:
            match = re.search(r'^((\\\\\.\\[^\\]+?\\)(.*?))\s*\|\s*(.*?)\s*$', line)
            if match:
                name = match.group(1)
                prefix = match.group(2)
                unique = match.group(4)

                items.append({
                    'id': unique.replace(prefix, ''),
                    'name': name,
                })

        return items

    def get_certificates(self):
        """
        Returns a list of certificates associated with a certain store

        Returns
        -------
        list: certificates

        Raises
        ------
        CryptoProError: when got an encryption error
        """

        for k in ('store_name',):
            assert getattr(self, k), '%s must be defined' % (k,)

        result = self._execute(
            "certmgr",
            "-list",
            "-store", "%(store_name)s"
        )

        lines = self._get_lines(result.stdout)
        items = []
        item = None
        key = None

        for line in lines:
            if re.search(r'^=+$', line):
                # Separator =========
                if item:
                    items.append(item)
                    item = None
                    key = None
            elif re.search(r'\d+\-+$', line):
                # Number: 1--------
                item = {}
            elif item is not None:
                match = re.search(r'^(.*?)\s+:\s+(.*?)\s*$', line)
                if match:
                    # Field: NAME : VALUE
                    key = match.group(1)
                    value = match.group(2)
                    item[key] = value
                elif key:
                    match = re.search(r'^\s{3,}(.*?)\s*$', line)
                    if match:
                        # Previous field continuation: VALUE
                        value = match.group(1)
                        if isinstance(item[key], list):
                            item[key].append(value)
                        else:
                            item[key] = [ item[key], value, ]

        return items

    def get_certificate_serial(self):
        """
        Returns a serial number of a certificate which is associated with a certain container

        Returns
        -------
        str: hex serial

        Raises
        ------
        CryptoProError: when got an encryption error
        """

        code = None
        containers = self.get_containers()
        for item in containers:
            if item['name'] == self.container_name:
                code = item['id']
                break

        if code is None:
            return None

        serial = None
        certificates = self.get_certificates()
        for item in certificates:
            if item['Container'] == code:
                serial = item['Serial']
                break

        if serial is None:
            return serial

        return serial.replace('0x', '').lower()

    def to_base64(self, value):
        """
        Returns a base64-encoded value

        Parameters
        ----------
        value[str, bytes]: a value to be encoded

        Returns
        -------
        str: base64 string
        """

        if isinstance(value, str):
            value = value.encode(self.encoding)
        return base64.b64encode(value).decode(self.encoding)

    def _execute(self, command, *args, **kwargs):
        """
        Returns a result of command execution

        Parameters
        ----------
        command[str]: a command to be executed
        *args: a list of arguments
        *kwargs: params to replace in args

        Returns
        -------
        subprocess.CompletedProcess: a result
        """

        kwargs.update({
            'sign_algorithm': self.sign_algorithm,
            'encryption_provider': self.encryption_provider,
            'container_name': self.container_name,
            'store_name': self.store_name,
        })

        command = self.prefix + command
        params = [ x % kwargs for x in args ]

        logger.debug('Executing %s with args: %s' % (command, params))

        res = self._proceed_command(command, *params)

        if res.returncode:
            logger.warning('Failed with code %d' % (res.returncode,))

        return res

    def _proceed_command(self, command, *args):
        """
        Proceeds a command

        Parameters
        ----------
        command[str]: a command to be executed
        *args: a list of arguments

        Returns
        -------
        subprocess.CompletedProcess: a result
        """

        return subprocess.run([command, *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def _create_temp_file(self, content=None):
        """
        Creates a temporary file with a certain content, closes it and returns a file name

        Parameters
        ----------
        content[str, bytes]: a file content

        Returns
        -------
        str: file name

        Raises
        ------
        OSError: when got OS filesystem error
        """

        file = tempfile.NamedTemporaryFile(mode='w+b', delete=False)
        if content is not None:
            if isinstance(content, str):
                content = content.encode(self.encoding)
            file.write(content)
        file.close()
        return file.name

    def _flush_temp_file(self, filename):
        """
        Reads a temporary file, removes it and returns a file content

        Parameters
        ----------
        filename[str]: a file name

        Returns
        -------
        bytes: file content

        Raises
        ------
        OSError: when got OS filesystem error
        """

        file = open(filename, mode='r+b')
        content = file.read()
        file.close()
        os.remove(file.name)
        return content

    def _get_lines(self, output):
        """
        Splits the output lines and returns a list

        Parameters
        ----------
        output[bytes]: a console output

        Returns
        -------
        list: a list of lines
        """

        return output.decode(self.encoding).split('\n')

    def _get_error(self, result):
        """
        Parses the cryptopro command output and tries to find an error number and description

        Parameters
        ----------
        result[subprocess.CompletedProcess]: an execution result

        Returns
        -------
        CryptoProError - an exception to raise
        """

        lines = self._get_lines(result.stderr)

        code = None
        text = None
        for line in lines:
            match = re.search(r'^Error\s+number\s+(0x[0-9a-f]+)\s+\((\d+)\)\.\s*$', line)
            if match:
                code = int(match.group(2))
            elif code is not None:
                text = line
                break

        if code is None:
            return CryptoProError('\n'.join(lines))
        if text is None:
            text = 'Error %d' % (code,)
        return CryptoProError(text, code)


__all__ = ('CryptoPro', 'CryptoProError')
