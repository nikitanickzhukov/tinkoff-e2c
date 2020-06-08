from cryptopro import CryptoPro
from tinkoff import Tinkoff


CRYPTOPRO = {
    'container_name': '\\\\.\\HDIMAGE\\xx-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
    'store_name': 'uMy',
    'encryption_provider': 80,
    'sign_algorithm': 'GOST12_256',
}
TINKOFF = {
    'terminal_key': '0000000000000E2C',
    'is_test': True,
}


def some_operations():
    cryptopro = CryptoPro(**CRYPTOPRO)
    tinkoff = Tinkoff(**TINKOFF, cryptopro=cryptopro)

    CLIENT_ID = 'myclient'
    ORDER_ID = 'myorder'
    AMOUNT = 100

    create_client_res = tinkoff.create_client(client_id=CLIENT_ID)
    get_client_res = tinkoff.get_client(client_id=CLIENT_ID)

    create_card_res = tinkoff.create_card(client_id=CLIENT_ID)
    print('Then go to {} and enter card data in browser'.format(create_card_res['url']))

    get_cards_res = tinkoff.get_cards(client_id=CLIENT_ID)
    first_card = get_cards_res[0]

    create_payment_res = tinkoff.create_payment(order_id=ORDER_ID, card_id=first_card['card_id'], amount=AMOUNT)
    proceed_payment_res = tinkoff.proceed_payment(
        payment_id=create_payment_res['payment_id'],
    )

    get_payment_res = tinkoff.get_payment(
        payment_id=create_payment_res['payment_id'],
    )

    delete_card_res = tinkoff.delete_card(client_id=CLIENT_ID, card_id=first_card['card_id'])

    delete_client_res = tinkoff.delete_client(client_id=CLIENT_ID)
