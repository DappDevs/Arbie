import json
from getpass import getpass

from eth_account import Account

from web3.auto.infura.ropsten import w3
from web3.middleware.signing import construct_sign_and_send_raw_middleware


def _keyfile_middleware(keyfile_path):
    with open(keyfile_path, 'r') as f:
        keyfile = json.loads(f.read())

    password = getpass("Please Input Keyfile Password ({}): ".format(keyfile_path))

    privateKey = Account.decrypt(keyfile, password)
    account = Account.privateKeyToAccount(privateKey)

    middleware = construct_sign_and_send_raw_middleware(privateKey)
    return account, middleware


class Bot:
    def __init__(self, _w3, _account):
        self.w3 = _w3
        self.account = _account
        self.


if __name__ == '__main__':
    account, _middleware = _keyfile_middleware('.your.keys')
    w3.middleware_stack.add(_middleware)

    bot = Bot(w3, account)
