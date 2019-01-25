class DeveloperAccount:
    def __init__(self, keyfile_path):
        import json
        from getpass import getpass

        from eth_account import Account

        from web3.auto.infura.ropsten import w3  # Ropsten testnet on Infura
        from web3.middleware.signing import construct_sign_and_send_raw_middleware

        with open(keyfile_path, 'r') as f:
            keyfile = json.loads(f.read())

        privateKey = None
        while not privateKey:
            try:
                password = getpass("Please Input Keyfile Password ({}): ".format(keyfile_path))
                privateKey = Account.decrypt(keyfile, password)
            except ValueError as e:
                print("Wrong Password! Try again!")

        self._account = Account.privateKeyToAccount(privateKey)
        self.w3 = w3  # Access to Ethereum API thru Infura

        # Allow web3 to autosign with account
        middleware = construct_sign_and_send_raw_middleware(privateKey)
        self.w3.middleware_stack.add(middleware)

    @property
    def address(self):
        return self._account.address


