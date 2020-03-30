from unittest import TestCase
from unittest.mock import MagicMock, patch
from requests.exceptions import HTTPError

from cryptopro import CryptoPro, CryptoProError
from tinkoff import Tinkoff, TinkoffError


CRYPTOPRO = {
    'container_name': '\\\\.\\HDIMAGE\\xx-xxxx',
    'store_name': 'uMy',
}
TINKOFF = {
    'terminal_key': 'test_key',
    'cryptopro': CRYPTOPRO,
}


class CryptoProTestCase(TestCase):
    def setUp(self):
        self.cryptopro = CryptoPro(**CRYPTOPRO)

    def tearDown(self):
        del self.cryptopro

    def test_hash(self):
        digest = self.cryptopro.get_hash('test string')
        print('get_digest', digest)

    def test_sign(self):
        sign = self.cryptopro.get_sign('test string')
        print('get_sign', sign)

    def test_serial(self):
        serial = self.cryptopro.get_certificate_serial()
        print('get_certificate_serial', serial)

    def test_containers(self):
        containers = self.cryptopro.get_containers()
        print('get_containers', containers)
        self.assertTrue(any([ x['name'] == self.cryptopro.container_name for x in containers ]))


class TinkoffTestCase(TestCase):
    def setUp(self):
        self.tinkoff = Tinkoff(**TINKOFF)

    def tearDown(self):
        del self.tinkoff

    @patch('tinkoff.Tinkoff._get_sign', return_value={})
    def test_create_payment(self, sign_mock):
        params = {
            'order_id': '1',
            'card_id': 1,
            'amount': 1,
            'data': {}
        }
        success = {
            'TerminalKey': self.tinkoff.terminal_key,
            'Success': True,
            'ErrorCode': '0',
            'PaymentId': '1',
            'Status': 'NEW',
        }
        fail = {
            'TerminalKey': self.tinkoff.terminal_key,
            'Success': False,
            'ErrorCode': '1',
            'Message': 'Some error',
            'Details': 'There is an error here',
        }

        response = self._get_mock_response(success)
        with patch('tinkoff.Tinkoff._proceed_request', return_value=response):
            result = self.tinkoff.create_payment(**params)
            self.assertEqual(result['id'], success['PaymentId'])

        response = self._get_mock_response(fail)
        with patch('tinkoff.Tinkoff._proceed_request', return_value=response):
            with self.assertRaises(TinkoffError) as error:
                result = self.tinkoff.create_payment(**params)
                self.assertEqual(error.code, fail['ErrorCode'])

    @patch('tinkoff.Tinkoff._get_sign', return_value={})
    def test_proceed_payment(self, sign_mock):
        params = {
            'id': '1',
        }
        success = {
            'TerminalKey': self.tinkoff.terminal_key,
            'Success': True,
            'ErrorCode': '0',
            'PaymentId': params['id'],
            'Status': 'COMPLETED',
        }
        fail = {
            'TerminalKey': self.tinkoff.terminal_key,
            'Success': False,
            'ErrorCode': '1',
            'Message': 'Some error',
            'Details': 'There is an error here',
        }

        response = self._get_mock_response(success)
        with patch('tinkoff.Tinkoff._proceed_request', return_value=response):
            result = self.tinkoff.proceed_payment(**params)
            self.assertEqual(result['id'], success['PaymentId'])

        response = self._get_mock_response(fail)
        with patch('tinkoff.Tinkoff._proceed_request', return_value=response):
            with self.assertRaises(TinkoffError) as error:
                result = self.tinkoff.proceed_payment(**params)
                self.assertEqual(error.code, fail['ErrorCode'])

    @patch('tinkoff.Tinkoff._get_sign', return_value={})
    def test_get_payment(self, sign_mock):
        params = {
            'id': '1',
        }
        success = {
            'TerminalKey': self.tinkoff.terminal_key,
            'Success': True,
            'ErrorCode': '0',
            'PaymentId': params['id'],
            'OrderId': '1',
            'Status': 'COMPLETED',
        }
        fail = {
            'TerminalKey': self.tinkoff.terminal_key,
            'Success': False,
            'ErrorCode': '1',
            'Message': 'Some error',
            'Details': 'There is an error here',
        }

        response = self._get_mock_response(success)
        with patch('tinkoff.Tinkoff._proceed_request', return_value=response):
            result = self.tinkoff.get_payment(**params)
            self.assertEqual(result['id'], success['PaymentId'])
            self.assertEqual(result['status'], success['Status'])

        response = self._get_mock_response(fail)
        with patch('tinkoff.Tinkoff._proceed_request', return_value=response):
            with self.assertRaises(TinkoffError) as error:
                result = self.tinkoff.get_payment(**params)
                self.assertEqual(error.code, fail['ErrorCode'])

    @patch('tinkoff.Tinkoff._get_sign', return_value={})
    def test_create_client(self, sign_mock):
        params = {
            'id': '1',
        }
        success = {
            'TerminalKey': self.tinkoff.terminal_key,
            'Success': True,
            'ErrorCode': '0',
            'CustomerKey': params['id'],
        }
        fail = {
            'TerminalKey': self.tinkoff.terminal_key,
            'Success': False,
            'ErrorCode': '1',
            'Message': 'Some error',
            'Details': 'There is an error here',
        }

        response = self._get_mock_response(success)
        with patch('tinkoff.Tinkoff._proceed_request', return_value=response):
            result = self.tinkoff.create_client(**params)
            self.assertEqual(result['id'], success['CustomerKey'])

        response = self._get_mock_response(fail)
        with patch('tinkoff.Tinkoff._proceed_request', return_value=response):
            with self.assertRaises(TinkoffError) as error:
                result = self.tinkoff.create_client(**params)
                self.assertEqual(error.code, fail['ErrorCode'])

    @patch('tinkoff.Tinkoff._get_sign', return_value={})
    def test_delete_client(self, sign_mock):
        params = {
            'id': '1',
        }
        success = {
            'TerminalKey': self.tinkoff.terminal_key,
            'Success': True,
            'ErrorCode': '0',
            'CustomerKey': params['id'],
        }
        fail = {
            'TerminalKey': self.tinkoff.terminal_key,
            'Success': False,
            'ErrorCode': '1',
            'Message': 'Some error',
            'Details': 'There is an error here',
        }

        response = self._get_mock_response(success)
        with patch('tinkoff.Tinkoff._proceed_request', return_value=response):
            result = self.tinkoff.delete_client(**params)
            self.assertEqual(result['id'], success['CustomerKey'])

        response = self._get_mock_response(fail)
        with patch('tinkoff.Tinkoff._proceed_request', return_value=response):
            with self.assertRaises(TinkoffError) as error:
                result = self.tinkoff.delete_client(**params)
                self.assertEqual(error.code, fail['ErrorCode'])

    @patch('tinkoff.Tinkoff._get_sign', return_value={})
    def test_get_client(self, sign_mock):
        params = {
            'id': '1',
        }
        success = {
            'TerminalKey': self.tinkoff.terminal_key,
            'Success': True,
            'ErrorCode': '0',
            'CustomerKey': params['id'],
        }
        fail = {
            'TerminalKey': self.tinkoff.terminal_key,
            'Success': False,
            'ErrorCode': '1',
            'Message': 'Some error',
            'Details': 'There is an error here',
        }

        response = self._get_mock_response(success)
        with patch('tinkoff.Tinkoff._proceed_request', return_value=response):
            result = self.tinkoff.get_client(**params)
            self.assertEqual(result['id'], success['CustomerKey'])

        response = self._get_mock_response(fail)
        with patch('tinkoff.Tinkoff._proceed_request', return_value=response):
            with self.assertRaises(TinkoffError) as error:
                result = self.tinkoff.get_client(**params)
                self.assertEqual(error.code, fail['ErrorCode'])

    @patch('tinkoff.Tinkoff._get_sign', return_value={})
    def test_create_card(self, sign_mock):
        params = {
            'client_id': '1',
            'check_type': 'NO',
        }
        success = {
            'TerminalKey': self.tinkoff.terminal_key,
            'Success': True,
            'ErrorCode': '0',
            'CustomerKey': params['client_id'],
            'RequestKey': '1',
        }
        success_status = 302
        success_header = {
            'Location': 'https://redirect.url/',
        }
        fail = {
            'TerminalKey': self.tinkoff.terminal_key,
            'Success': False,
            'ErrorCode': '1',
            'Message': 'Some error',
            'Details': 'There is an error here',
        }

        response = self._get_mock_response(success, success_status, success_header)
        with patch('tinkoff.Tinkoff._proceed_request', return_value=response):
            result = self.tinkoff.create_card(**params)
            self.assertEqual(result['request_id'], success['RequestKey'])
            self.assertEqual(result['url'], success_header['Location'])

        response = self._get_mock_response(fail)
        with patch('tinkoff.Tinkoff._proceed_request', return_value=response):
            with self.assertRaises(TinkoffError) as error:
                result = self.tinkoff.create_card(**params)
                self.assertEqual(error.code, fail['ErrorCode'])

    @patch('tinkoff.Tinkoff._get_sign', return_value={})
    def test_delete_card(self, sign_mock):
        params = {
            'id': 1,
            'client_id': '1',
        }
        success = {
            'TerminalKey': self.tinkoff.terminal_key,
            'Success': True,
            'ErrorCode': '0',
            'CardId': params['id'],
            'CustomerKey': params['client_id'],
            'Status': 'D',
        }
        fail = {
            'TerminalKey': self.tinkoff.terminal_key,
            'Success': False,
            'ErrorCode': '1',
            'Message': 'Some error',
            'Details': 'There is an error here',
        }

        response = self._get_mock_response(success)
        with patch('tinkoff.Tinkoff._proceed_request', return_value=response):
            result = self.tinkoff.delete_card(**params)
            self.assertEqual(result['id'], success['CardId'])

        response = self._get_mock_response(fail)
        with patch('tinkoff.Tinkoff._proceed_request', return_value=response):
            with self.assertRaises(TinkoffError) as error:
                result = self.tinkoff.delete_card(**params)
                self.assertEqual(error.code, fail['ErrorCode'])

    @patch('tinkoff.Tinkoff._get_sign', return_value={})
    def test_get_cards(self, sign_mock):
        params = {
            'client_id': '1',
        }
        success = [
            {
                'CardId': 1,
                'Pan': '1111 22** **** 4444',
                'RebillID': 1,
                'Status': 'A',
                'CardType': 1,
                'ExpDate': '0220',
            }, {
                'CardId': 2,
                'Pan': '4444 33** **** 1111',
                'RebillID': 2,
                'Status': 'I',
                'CardType': 2,
            }
        ]
        fail = {
            'TerminalKey': self.tinkoff.terminal_key,
            'Success': False,
            'ErrorCode': '1',
            'Message': 'Some error',
            'Details': 'There is an error here',
        }

        response = self._get_mock_response(success)
        with patch('tinkoff.Tinkoff._proceed_request', return_value=response):
            items = self.tinkoff.get_cards(**params)
            self.assertEqual(len(items), len(success))
            for i in range(len(items)):
                self.assertEqual(items[i]['id'], success[i]['CardId'])
                self.assertEqual(items[i]['pan'], success[i]['Pan'])
                self.assertEqual(items[i]['status'], success[i]['Status'])

        response = self._get_mock_response(fail)
        with patch('tinkoff.Tinkoff._proceed_request', return_value=response):
            with self.assertRaises(TinkoffError) as error:
                result = self.tinkoff.get_cards(**params)
                self.assertEqual(error.code, fail['ErrorCode'])

    def _get_mock_response(self, json, status_code=200, headers={}):
        def raise_for_status():
            if status_code >= 400: raise HTTPError
        response = MagicMock()
        response.json = MagicMock(return_value=json)
        response.status_code = status_code
        response.headers = headers
        response.raise_for_status = MagicMock(side_effect=raise_for_status)
        return response


if __name__ == '__main__':
    unittest.main()
