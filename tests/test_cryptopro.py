from unittest import TestCase
from unittest.mock import MagicMock, patch

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

        response = self._get_mock_response()
        with patch('cryptopro.CryptoPro._proceed_command', return_value=response):
            with patch('cryptopro.CryptoPro._create_temp_file', return_value=tempfile):
                with patch('cryptopro.CryptoPro._flush_temp_file', return_value=test_result):
                    result = self.cryptopro.get_hash(test_source)
                    self.assertEqual(result, test_result)

    def test_get_sign(self):
        test_source = b'test source'
        test_result = b'test result'
        tempfile = '/tmp/cryptopro.unittest'

        response = self._get_mock_response()
        with patch('cryptopro.CryptoPro._proceed_command', return_value=response):
            with patch('cryptopro.CryptoPro._create_temp_file', return_value=tempfile):
                with patch('cryptopro.CryptoPro._flush_temp_file', return_value=test_result):
                    result = self.cryptopro.get_sign(test_source)
                    self.assertEqual(result, test_result)

    def test_get_containers(self):
        result_out = 'AcquireContext: OK. HCRYPTPROV: 12345678\n' + \
                     '\\\\.\\HDIMAGE\\xx-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx|\\\\.\\HDIMAGE\\HDIMAGE\\\\xx-xxxxf.000\\XXXX\n' + \
                     '\\\\.\\HDIMAGE\\yy-yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy|\\\\.\\HDIMAGE\\HDIMAGE\\\\yy-yyyyf.000\\YYYY\n' + \
                     '[ErrorCode: 0x00000000]\n'

        response = self._get_mock_response(result_out.encode(self.cryptopro.encoding))
        with patch('cryptopro.CryptoPro._proceed_command', return_value=response):
            items = self.cryptopro.get_containers()
            self.assertEqual(len(items), 2)
            self.assertEqual(items[0]['id'], 'HDIMAGE\\\\xx-xxxxf.000\\XXXX')
            self.assertEqual(items[0]['name'], '\\\\.\\HDIMAGE\\xx-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx')

    def test_crypto_error(self):
        tempfile = '/tmp/cryptopro.unittest'
        test_source = b'test source'
        error_code = 123
        error_text = 'Some error'
        error_out = 'An error occurred in running the program.\n' + \
                    'Error number %s (0x%x).\n%s\n' % (error_code, error_code, error_text)

        response = self._get_mock_response(b'', error_out.encode(self.cryptopro.encoding), error_code)
        with patch('cryptopro.CryptoPro._proceed_command', return_value=response):
            with patch('cryptopro.CryptoPro._create_temp_file', return_value=tempfile):
                with patch('cryptopro.CryptoPro._flush_temp_file', return_value=None):
                    with self.assertRaises(CryptoProError) as error:
                        result = self.cryptopro.get_hash(test_source)
                        self.assertEqual(error.code, error_code)

    def _get_mock_response(self, stdout=b'', stderr=b'', returncode=0):
        response = MagicMock()
        response.stdout = stdout
        response.stderr = stderr
        response.returncode = returncode
        return response
