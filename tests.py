import unittest
import random
import string

from .cryptopro import CryptoPro, CryptoProError
from .tinkoff import Tinkoff, TinkoffError


CRYPTOPRO = {
    'container_name': '',
    'store_name': '',
}
TINKOFF = {
    'terminal_key': '',
    'cryptopro': CRYPTOPRO,
}


class CryptoProTestCase(unittest.TestCase):
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


class TinkoffTestCase(unittest.TestCase):
    def setUp(self):
        self.client_id = 'unittest.client'
        self.tinkoff = Tinkoff(**TINKOFF)
        self.tinkoff.create_client(id=self.client_id)

    def tearDown(self):
        self.tinkoff.delete_client(id=self.client_id)
        del self.tinkoff
        del self.client_id

    def test_client(self):
        client_id = self.client_id + '.test'

        with self.assertRaises(TinkoffError):
            self.tinkoff.get_client(id=client_id)

        result = self.tinkoff.create_client(id=client_id)
        self.assertEqual(result['id'], client_id)

        with self.assertRaises(TinkoffError):
            self.tinkoff.create_client(id=client_id)

        result = self.tinkoff.get_client(id=client_id)
        self.assertEqual(result['id'], client_id)

        self.tinkoff.delete_client(id=client_id)

        with self.assertRaises(TinkoffError):
            self.tinkoff.get_client(id=client_id)

        with self.assertRaises(TinkoffError):
            self.tinkoff.delete_client(id=client_id)

    def test_card(self):
        result = self.tinkoff.create_card(self.client_id)
        self.assertTrue(result['url'])


if __name__ == '__main__':
    unittest.main()
