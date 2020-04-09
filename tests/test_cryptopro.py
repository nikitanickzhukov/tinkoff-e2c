from unittest import TestCase
from unittest.mock import patch

from cryptopro import CryptoPro, CryptoProError


CRYPTOPRO = {
    'container_name': '\\\\.\\HDIMAGE\\xx-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
    'store_name': 'uMy',
}


class CryptoProTestCase(TestCase):
    def setUp(self):
        self.cryptopro = CryptoPro(**CRYPTOPRO)

    def tearDown(self):
        del self.cryptopro

    def test_get_hash(self):
        test_source = b'test source'
        test_result = b'test result'
        tempfile = '/tmp/cryptopro.unittest'

        command_patch = self._get_command_patch()
        with patch('cryptopro.CryptoPro._proceed_command', **command_patch):
            with patch('cryptopro.CryptoPro._create_temp_file', return_value=tempfile):
                with patch('cryptopro.CryptoPro._flush_temp_file', return_value=test_result):
                    result = self.cryptopro.get_hash(test_source)
                    self.assertEqual(result, test_result)

    def test_get_sign(self):
        test_source = b'test source'
        test_result = b'test result'
        tempfile = '/tmp/cryptopro.unittest'

        command_patch = self._get_command_patch()
        with patch('cryptopro.CryptoPro._proceed_command', **command_patch):
            with patch('cryptopro.CryptoPro._create_temp_file', return_value=tempfile):
                with patch('cryptopro.CryptoPro._flush_temp_file', return_value=test_result):
                    result = self.cryptopro.get_sign(test_source)
                    self.assertEqual(result, test_result)

    def test_get_containers(self):
        result_out = 'AcquireContext: OK. HCRYPTPROV: 12345678\n' + \
                     '\\\\.\\HDIMAGE\\xx-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx|\\\\.\\HDIMAGE\\HDIMAGE\\\\xx-xxxxf.000\\XXXX\n' + \
                     '\\\\.\\HDIMAGE\\yy-yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy|\\\\.\\HDIMAGE\\HDIMAGE\\\\yy-yyyyf.000\\YYYY\n' + \
                     '[ErrorCode: 0x00000000]\n'

        command_patch = self._get_command_patch(result_out.encode(self.cryptopro.encoding))
        with patch('cryptopro.CryptoPro._proceed_command', **command_patch):
            items = self.cryptopro.get_containers()
            self.assertEqual(len(items), 2)
            self.assertEqual(items[0]['id'], 'HDIMAGE\\\\xx-xxxxf.000\\XXXX')
            self.assertEqual(items[0]['name'], '\\\\.\\HDIMAGE\\xx-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx')

    def test_get_certificates(self):
        result_out = '=============================================================================\n' + \
                     '1-------\n' + \
                     'Issuer              : E=cpca@cryptopro.ru\n' + \
                     'Subject             : E=test@test.ru\n' + \
                     'Serial              : 0x0000000000000000000000000000000000\n' + \
                     'Container           : HDIMAGE\\\\xx-xxxxf.000\\XXXX\n' + \
                     'CDP                 : http://cdp.cryptopro.ru/cdp/0000.crl\n' + \
                     'CDP                 : http://cpca20.cryptopro.ru/cdp/0000.crl\n' + \
                     'Extended Key Usage  : 1.3.6.1.5.5.7.3.2\n' + \
                     '                      1.3.6.1.5.5.7.3.4\n' + \
                     '=============================================================================\n' + \
                     '2-------\n' + \
                     'Issuer              : E=cpca@cryptopro.ru\n' + \
                     'Subject             : E=test@test.ru\n' + \
                     'Serial              : 0x1111111111111111111111111111111111\n' + \
                     'Container           : HDIMAGE\\\\yy-yyyyf.000\\YYYY\n' + \
                     'Extended Key Usage  : 1.3.6.1.5.5.7.3.2\n' + \
                     '=============================================================================\n' + \
                     '[ErrorCode: 0x00000000]\n'

        command_patch = self._get_command_patch(result_out.encode(self.cryptopro.encoding))
        with patch('cryptopro.CryptoPro._proceed_command', **command_patch):
            items = self.cryptopro.get_certificates()
            self.assertEqual(len(items), 2)
            self.assertEqual(items[0]['Serial'], '0x0000000000000000000000000000000000')
            self.assertEqual(items[0]['Container'], 'HDIMAGE\\\\xx-xxxxf.000\\XXXX')
            self.assertEqual(items[0]['CDP'], ['http://cdp.cryptopro.ru/cdp/0000.crl', 'http://cpca20.cryptopro.ru/cdp/0000.crl'])
            self.assertEqual(items[0]['Extended Key Usage'], ['1.3.6.1.5.5.7.3.2', '1.3.6.1.5.5.7.3.4'])

    def test_get_certificate_serial(self):
        containers = [
            {
                'id': 'HDIMAGE\\\\xx-xxxxf.000\\XXXX',
                'name': '\\\\.\\HDIMAGE\\xx-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
            }, {
                'id': 'HDIMAGE\\\\yy-yyyyf.000\\YYYY',
                'name': '\\\\.\\HDIMAGE\\yy-yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy',
            }
        ]
        certificates = [
            {
                'Serial': '0x0000000000000000000000000000000000',
                'Container': 'HDIMAGE\\\\xx-xxxxf.000\\XXXX',
            }, {
                'Serial': '0x1111111111111111111111111111111111',
                'Container': 'HDIMAGE\\\\yy-yyyyf.000\\YYYY',
            }
        ]

        with patch('cryptopro.CryptoPro.get_containers', return_value=containers):
            with patch('cryptopro.CryptoPro.get_certificates', return_value=certificates):
                serial = self.cryptopro.get_certificate_serial()
                self.assertEqual(serial, certificates[0]['Serial'].replace('0x', '').lower())

    def test_crypto_error(self):
        tempfile = '/tmp/cryptopro.unittest'
        test_source = b'test source'
        error_code = 123
        error_text = 'Some error'
        error_out = 'An error occurred in running the program.\n' + \
                    'Error number %s (0x%x).\n%s\n' % (error_code, error_code, error_text)

        command_patch = self._get_command_patch(b'', error_out.encode(self.cryptopro.encoding), 1)
        with patch('cryptopro.CryptoPro._proceed_command', **command_patch):
            with patch('cryptopro.CryptoPro._create_temp_file', return_value=tempfile):
                with patch('cryptopro.CryptoPro._flush_temp_file', return_value=None):
                    with self.assertRaises(CryptoProError) as error:
                        result = self.cryptopro.get_hash(test_source)
                        self.assertEqual(error.code, error_code)

    def _get_command_patch(self, stdout=b'', stderr=b'', returncode=0):
        def side_effect(*args, **kwargs):
            if returncode:
                raise self.cryptopro._get_error(stderr)
            return stdout
        return {
            'side_effect': side_effect,
        }
