from unittest import TestCase
from unittest.mock import patch
from requests.exceptions import HTTPError

from tinkoff import Tinkoff, TinkoffError
from .test_cryptopro import CRYPTOPRO


TINKOFF = {
    'terminal_key': 'test_key',
    'cryptopro': CRYPTOPRO,
    'is_test': True,
}
SIGN_VALUE = {
    'DigestValue': 'base64digest',
    'SignatureValue': 'base64sign',
    'X509SerialNumber': 'hexserial',
}


@patch('tinkoff.Tinkoff._get_sign', return_value=SIGN_VALUE)
class TinkoffTestCase(TestCase):
    def setUp(self):
        self.tinkoff = Tinkoff(**TINKOFF)

    def tearDown(self):
        del self.tinkoff

    def test_real_request(self, sign_mock):
        params = {
            'order_id': '1',
            'card_id': 1,
            'amount': 1,
            'data': {}
        }
        with self.assertRaises(TinkoffError) as e:
            result = self.tinkoff.create_payment(**params)
            self.assertEqual(e.code, '9999')

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

        request_patch = self._get_request_patch(success)
        with patch('tinkoff.Tinkoff._proceed_request', **request_patch):
            result = self.tinkoff.create_payment(**params)
            self.assertEqual(result['id'], success['PaymentId'])

        request_patch = self._get_request_patch(fail)
        with patch('tinkoff.Tinkoff._proceed_request', **request_patch):
            with self.assertRaises(TinkoffError) as error:
                result = self.tinkoff.create_payment(**params)
                self.assertEqual(error.code, fail['ErrorCode'])

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

        request_patch = self._get_request_patch(success)
        with patch('tinkoff.Tinkoff._proceed_request', **request_patch):
            result = self.tinkoff.proceed_payment(**params)
            self.assertEqual(result['id'], success['PaymentId'])

        request_patch = self._get_request_patch(fail)
        with patch('tinkoff.Tinkoff._proceed_request', **request_patch):
            with self.assertRaises(TinkoffError) as error:
                result = self.tinkoff.proceed_payment(**params)
                self.assertEqual(error.code, fail['ErrorCode'])

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

        request_patch = self._get_request_patch(success)
        with patch('tinkoff.Tinkoff._proceed_request', **request_patch):
            result = self.tinkoff.get_payment(**params)
            self.assertEqual(result['id'], success['PaymentId'])
            self.assertEqual(result['status'], success['Status'])

        request_patch = self._get_request_patch(fail)
        with patch('tinkoff.Tinkoff._proceed_request', **request_patch):
            with self.assertRaises(TinkoffError) as error:
                result = self.tinkoff.get_payment(**params)
                self.assertEqual(error.code, fail['ErrorCode'])

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

        request_patch = self._get_request_patch(success)
        with patch('tinkoff.Tinkoff._proceed_request', **request_patch):
            result = self.tinkoff.create_client(**params)
            self.assertEqual(result['id'], success['CustomerKey'])

        request_patch = self._get_request_patch(fail)
        with patch('tinkoff.Tinkoff._proceed_request', **request_patch):
            with self.assertRaises(TinkoffError) as error:
                result = self.tinkoff.create_client(**params)
                self.assertEqual(error.code, fail['ErrorCode'])

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

        request_patch = self._get_request_patch(success)
        with patch('tinkoff.Tinkoff._proceed_request', **request_patch):
            result = self.tinkoff.delete_client(**params)
            self.assertEqual(result['id'], success['CustomerKey'])

        request_patch = self._get_request_patch(fail)
        with patch('tinkoff.Tinkoff._proceed_request', **request_patch):
            with self.assertRaises(TinkoffError) as error:
                result = self.tinkoff.delete_client(**params)
                self.assertEqual(error.code, fail['ErrorCode'])

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

        request_patch = self._get_request_patch(success)
        with patch('tinkoff.Tinkoff._proceed_request', **request_patch):
            result = self.tinkoff.get_client(**params)
            self.assertEqual(result['id'], success['CustomerKey'])

        request_patch = self._get_request_patch(fail)
        with patch('tinkoff.Tinkoff._proceed_request', **request_patch):
            with self.assertRaises(TinkoffError) as error:
                result = self.tinkoff.get_client(**params)
                self.assertEqual(error.code, fail['ErrorCode'])

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

        request_patch = self._get_request_patch(success, success_status, success_header)
        with patch('tinkoff.Tinkoff._proceed_request', **request_patch):
            result = self.tinkoff.create_card(**params)
            self.assertEqual(result['request_id'], success['RequestKey'])
            self.assertEqual(result['url'], success_header['Location'])

        request_patch = self._get_request_patch(fail)
        with patch('tinkoff.Tinkoff._proceed_request', **request_patch):
            with self.assertRaises(TinkoffError) as error:
                result = self.tinkoff.create_card(**params)
                self.assertEqual(error.code, fail['ErrorCode'])

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

        request_patch = self._get_request_patch(success)
        with patch('tinkoff.Tinkoff._proceed_request', **request_patch):
            result = self.tinkoff.delete_card(**params)
            self.assertEqual(result['id'], success['CardId'])

        request_patch = self._get_request_patch(fail)
        with patch('tinkoff.Tinkoff._proceed_request', **request_patch):
            with self.assertRaises(TinkoffError) as error:
                result = self.tinkoff.delete_card(**params)
                self.assertEqual(error.code, fail['ErrorCode'])

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

        request_patch = self._get_request_patch(success)
        with patch('tinkoff.Tinkoff._proceed_request', **request_patch):
            items = self.tinkoff.get_cards(**params)
            self.assertEqual(len(items), len(success))
            for i in range(len(items)):
                self.assertEqual(items[i]['id'], success[i]['CardId'])
                self.assertEqual(items[i]['pan'], success[i]['Pan'])
                self.assertEqual(items[i]['status'], success[i]['Status'])

        request_patch = self._get_request_patch(fail)
        with patch('tinkoff.Tinkoff._proceed_request', **request_patch):
            with self.assertRaises(TinkoffError) as error:
                result = self.tinkoff.get_cards(**params)
                self.assertEqual(error.code, fail['ErrorCode'])

    def test_server_error(self, sign_mock):
        params = {
            'order_id': '1',
            'card_id': 1,
            'amount': 1,
            'data': {}
        }

        request_patch = self._get_request_patch(None, 500)
        with patch('tinkoff.Tinkoff._proceed_request', **request_patch):
            with self.assertRaises(HTTPError):
                result = self.tinkoff.create_payment(**params)

    def _get_request_patch(self, result, status=200, headers=None):
        if headers is None:
            headers = {}
        def side_effect(*args, **kwargs):
            if status >= 400:
                raise HTTPError
            return (result, status, headers)
        return {
            'side_effect': side_effect,
        }
