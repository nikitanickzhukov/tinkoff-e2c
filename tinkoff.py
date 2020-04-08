import requests

from cryptopro import CryptoPro, CryptoProError

import logging
logger = logging.getLogger(__name__)


PAYMENT_STATUS_MAPPING = {
    'NEW': 'Платеж зарегистрирован в шлюзе, но его обработка в процессинге не начата',
    'CHECKING': 'Платеж на этапе проверки данных',
    'CHECKED': 'Данные проверены',
    'COMPLETING': 'Начато зачисление денежных средств',
    'COMPLETED': 'Денежные средства зачислены на карту получателя',
    'REJECTED': 'Платеж отклонен банком',
    'PROCESSING': 'На стадии обработки',
    'UNKNOWN': 'Статус не определен',
}
CARD_CHECK_TYPES = (
    ('NO', 'Сохранить карту без проверок'),
    ('HOLD', 'При сохранении сделать списание, а затем отмену на 1 руб.'),
    ('3DS', 'При сохранении карты выполнить проверку 3DS и выполнить списание, а затем отмену на 1 руб.'),
    ('3DSHOLD', 'При привязке выполняем проверку, поддерживает карта 3DS или нет. \
      Если да, выполняем списание, а затем отмену на 1 руб. Если нет, то аналогично на сумму от 100 до 199 коп.'),
)
CARD_STATUS_MAPPING = {
    'A': 'Активная',
    'I': 'Неактивная',
    'E': 'Срок действия истек',
    'D': 'Удалена',
}
CARD_TYPE_MAPPING = {
    0: 'Карта списания',
    1: 'Карта пополнения',
    2: 'Карта списания и пополнения',
}


class TinkoffError(Exception):
    def __init__(self, message, code='-1'):
        super().__init__(message, code)
        self.message = message
        self.code = code

    def __str__(self):
        return '{}: {}'.format(self.code, self.message)


class Tinkoff():
    """
    A class for Tinkoff's E2C operations

    Methods
    -------
    create_payment()
        register a new payment
    proceed_payment()
        proceed a registered payment by id
    get_payment()
        get payment status by id
    create_client()
        create a new client by id
    delete_client()
        delete an existing client by id
    get_client()
        get a client info by id
    create_card()
        create a card by client id
    delete_card()
        delete a card by id and client id
    get_cards()
        get a list of cards by client id
    get_card_check_types()
        get a list of available card check types
    """

    test_url = 'https://rest-api-test.tinkoff.ru/e2c/'
    prod_url = 'https://securepay.tinkoff.ru/e2c/'

    def __init__(self, terminal_key, cryptopro, is_test=False):
        """
        Parameters
        ----------
        terminal_key[str]: the terminal key (got from bank)
        cryptopro[dict]: cryptopro settings (see cryptopro.CryptoPro init parameters)
        is_test[bool]: use test endpoint for requests
        """

        assert terminal_key, 'Terminal key must be defined'

        self.terminal_key = terminal_key
        self.cryptopro = cryptopro
        self.is_test = is_test

    def create_payment(self, order_id, card_id, amount, client_id=None, data=None):
        """
        Creates a payment

        Parameters
        ----------
        order_id[str]: `OrderId` (in user's namespace)
        card_id[int]: `CardId`
        amount[int, float]: `Amount` (in basic units: roubles, USD, etc)
        client_id[str]: `ClientId`
        data[dict]: `DATA`

        Returns
        -------
        dict: payment data:
            - id[int] - `PaymentId`
            - status[str] - `Status`
            - status_name[str] - `Status` description
            - url[str] - `PaymentURL` or `Location` header when got a 3xx status

        Raises
        ------
        CryptoProError: when got an encryption error
        HTTPError: when got a request error
        TinkoffError: when got an error from the bank
        """

        # ERROR: There is a signature error if `client_id` is passed

        request = {
            'OrderId': order_id,
            'CardId': card_id,
            'Amount': self._process_amount(amount),
        }
        if client_id is not None:
            request['ClientId'] = client_id
        if data is not None:
            request['DATA'] = self._join_data(data)

        response = self._request('POST', 'Init', data=request)
        result = {
            'id': response['PaymentId'],
            'status': response['Status'],
            'status_name': PAYMENT_STATUS_MAPPING.get(response['Status']),
        }
        if 'PaymentURL' in response:
            result['url'] = response['PaymentURL']
        elif 'URL' in response:
            result['url'] = response['URL']
        return result

    def proceed_payment(self, id):
        """
        Proceeds a payment

        Parameters
        ----------
        id[int]: `PaymentId`

        Returns
        -------
        dict: payment info:
            - id[int] - `PaymentId`
            - status[str] - `Status`
            - status_name[str] - `Status` description

        Raises
        ------
        CryptoProError: when got an encryption error
        HTTPError: when got a request error
        TinkoffError: when got an error from the bank
        """

        request = {
            'PaymentId': id,
        }
        response = self._request('POST', 'Payment', data=request)
        return {
            'id': response['PaymentId'],
            'status': response['Status'],
            'status_name': PAYMENT_STATUS_MAPPING.get(response['Status']),
        }

    def get_payment(self, id):
        """
        Returns a payment info

        Parameters
        ----------
        id[int]: `PaymentId`

        Returns
        -------
        dict: payment info:
            - id[int] - `PaymentId`
            - status[str] - `Status`
            - status_name[str] - `Status` description

        Raises
        ------
        CryptoProError: when got an encryption error
        HTTPError: when got a request error
        TinkoffError: when got an error from the bank
        """

        request = {
            'PaymentId': id,
        }
        response = self._request('POST', 'GetState', data=request)
        return {
            'id': response['PaymentId'],
            'status': response['Status'],
            'status_name': PAYMENT_STATUS_MAPPING.get(response['Status']),
        }

    def create_client(self, id, email=None, phone=None):
        """
        Creates a client

        Parameters
        ----------
        id[str]: `CustomerKey`
        email[str]: `Email`
        phone[str]: `Phone`

        Returns
        -------
        dict: client info:
            - id[str] - `CustomerKey`

        Raises
        ------
        CryptoProError: when got an encryption error
        HTTPError: when got a request error
        TinkoffError: when got an error from the bank
        """

        request = {
            'CustomerKey': id,
        }
        if email is not None:
            request['Email'] = email
        if phone is not None:
            request['Phone'] = phone
        response = self._request('POST', 'AddCustomer', data=request)
        return {
            'id': response['CustomerKey'],
        }

    def delete_client(self, id):
        """
        Deletes a client

        Parameters
        ----------
        id[str]: `CustomerKey`

        Returns
        -------
        dict: client info:
            - id[str] - `CustomerKey`

        Raises
        ------
        CryptoProError: when got an encryption error
        HTTPError: when got a request error
        TinkoffError: when got an error from the bank
        """

        request = {
            'CustomerKey': id,
        }
        response = self._request('POST', 'RemoveCustomer', data=request)
        return {
            'id': response['CustomerKey'],
        }

    def get_client(self, id):
        """
        Returns a client info

        Parameters
        ----------
        id[str]: `CustomerKey`

        Returns
        -------
        dict: client info:
            - id[str] - `CustomerKey`
            - email[str] - `Email`
            - phone[str] - `Phone`

        Raises
        ------
        CryptoProError: when got an encryption error
        HTTPError: when got a request error
        TinkoffError: when got an error from the bank
        """

        request = {
            'CustomerKey': id,
        }
        response = self._request('POST', 'GetCustomer', data=request)
        result = {
            'id': response['CustomerKey'],
        }
        if 'Email' in response:
            result['email'] = response['Email']
        if 'Phone' in response:
            result['phone'] = response['Phone']
        return result

    def create_card(self, client_id, check_type=None, comment=None, form_type=None):
        """
        Returns an URL to go for creating a card

        Parameters
        ----------
        client_id[str]: `CustomerKey`
        check_type[str] - `CheckType`
        comment[str] - `Description`
        form_type[str] - `PayForm`

        Returns
        -------
        dict: request info:
            - request_id[str] - `RequestKey`
            - url[str] - `PaymentURL` or `Location` header when got a 3xx status

        Raises
        ------
        CryptoProError: when got an encryption error
        HTTPError: when got a request error
        TinkoffError: when got an error from the bank
        """

        # ERROR: There is a signature error if comment and/or form_type are passed

        request = {
            'CustomerKey': client_id,
        }
        if check_type is not None:
            request['CheckType'] = check_type
        if comment is not None:
            request['Description'] = comment
        if form_type is not None:
            request['PayForm'] = form_type
        response = self._request('POST', 'AddCard', data=request, allow_redirects=False)
        result = {
            'request_id': response['RequestKey'],
        }
        if 'PaymentURL' in response:
            result['url'] = response['PaymentURL']
        elif 'URL' in response:
            result['url'] = response['URL']
        return result

    def delete_card(self, id, client_id):
        """
        Updates card status to `D` (deleted)

        Parameters
        ----------
        id[int]: `CardId`
        client_id[str]: `CustomerKey`

        Returns
        -------
        dict: card info:
            - id[int] - `CardId`
            - status[str] - `Status`
            - status_name[str] - `Status` description

        Raises
        ------
        CryptoProError: when got an encryption error
        HTTPError: when got a request error
        TinkoffError: when got an error from the bank
        """

        request = {
            'CardId': id,
            'CustomerKey': client_id,
        }
        response = self._request('POST', 'RemoveCard', data=request)
        return {
            'id': response['CardId'],
            'status': response['Status'],
            'status_name': CARD_STATUS_MAPPING.get(response['Status']),
        }

    def get_cards(self, client_id):
        """
        Returns a list of client's cards

        Parameters
        ----------
        client_id[str]: `CustomerKey`

        Returns
        -------
        list[dict]: cards:
            - id[int] - `CardId`
            - status[str] - `Status`
            - status_name[str] - `Status` description
            - type[int] -  `CardType`,
            - type_name[str] - `CardType` description
            - pan[str] - `Pan` (masked)
            - rebill_id[int] - `RebillID`
            - expires[str] - `ExpDate`
            - is_active[bool] - card has `A` (active) `Status`

        Raises
        ------
        CryptoProError: when got an encryption error
        HTTPError: when got a request error
        TinkoffError: when got an error from the bank
        """

        request = {
            'CustomerKey': client_id,
        }
        response = self._request('POST', 'GetCardList', data=request)
        return [ {
            'id': x['CardId'],
            'type': x['CardType'],
            'type_name': CARD_TYPE_MAPPING.get(x['CardType']),
            'pan': x['Pan'],
            'status': x['Status'],
            'status_name': CARD_STATUS_MAPPING.get(x['Status']),
            'rebill_id': x.get('RebillID'),
            'expires': x.get('ExpDate'),
            'is_active': (x['Status'] == 'A'),
        } for x in response['items'] ]

    def get_card_check_types(self):
        """
        Returns a list of available options for card checking

        Returns
        -------
        list[dict]: cards:
            - code[str] - code name
            - name[str] - description
        """

        return [ { 'code': x[0], 'name': x[1] } for x in CARD_CHECK_TYPES ]

    def _process_amount(self, value):
        return int(value * 100)

    def _join_data(self, data):
        return '|'.join([ '%s=%s' % (x, data[x]) for x in data ])

    def _request(self, method, url, **kwargs):
        method, url, params = self._prepare_request(method, url, **kwargs)

        logger.debug('Request %s to URL %s with args: %s' % (method, url, str(kwargs)))
        response = self._proceed_request(method, url, **params)

        try:
            response.raise_for_status()
        except Exception as e:
            logger.exception('Failed with status %d' % (response.status_code,))
            raise e

        return self._prepare_response(response)

    def _prepare_request(self, method, url, **kwargs):
        kwargs.setdefault('data', {})
        kwargs.setdefault('headers', {})

        kwargs['data'].update({'TerminalKey': self.terminal_key})
        kwargs['data'].update(self._get_sign(kwargs['data']))
        kwargs['headers'].update({'Content-Type': 'application/x-www-form-urlencoded'})
        url = self.url + url

        return method, url, kwargs

    def _proceed_request(self, method, url, **kwargs):
        return requests.request(method, url, **kwargs)

    def _prepare_response(self, response):
        result = response.json()
        logger.debug('Got response: %s', result)

        if isinstance(result, dict):
            if not result['Success']:
                logger.warning('Failed with result: %s', result)
                message = ' '.join([ x for x in [ result.get('Details'), result.get('Message') ] if x ])
                code = result.get('ErrorCode', '-1')
                raise TinkoffError(message, code)
        elif isinstance(result, list):
            result = {
                'items': result,
            }

        if 300 <= response.status_code <= 399:
            result['URL'] = response.headers['Location']

        return result

    def _get_sign(self, data):
        logger.debug('Sign data: %s', data)

        content = ''.join([ str(data[x]) for x in sorted(data.keys()) ])

        logger.debug('Sign string: %s', content)

        try:
            digest = self.cp.get_hash(content)
            digest_b64 = self.cp.to_base64(digest)
        except CryptoProError as e:
            logger.exception('Cannot generate digest: error %d', e.code)
            raise e

        logger.debug('Hash: %s', digest_b64)

        try:
            sign = self.cp.get_sign(digest)
            sign_b64 = self.cp.to_base64(sign)
        except CryptoProError as e:
            logger.exception('Cannot generate signature: error %d', e.code)
            raise e

        logger.debug('Sign: %s' % (sign_b64,))

        try:
            serial = self.cp.get_certificate_serial()
        except CryptoProError as e:
            logger.exception('Cannot get certificate serial: error %d', e.code)
            raise e

        logger.debug('Serial: %s', serial)

        return {
            'DigestValue': digest_b64,
            'SignatureValue': sign_b64,
            'X509SerialNumber': serial,
        }

    @property
    def url(self):
        return self.test_url if self.is_test else self.prod_url

    @property
    def cp(self):
        if not hasattr(self, '__cp'):
            setattr(self, '__cp', CryptoPro(**self.cryptopro))
        return getattr(self, '__cp')


__all__ = ('Tinkoff', 'TinkoffError')
