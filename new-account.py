import json
import getpass
import pyqrcode

from eth_account import Account

# Create a branch new account with a random private key
account = Account.create(extra_entropy=getpass.getpass("Please smash the keyboard and press [ENTER] when ready :) "))
print()

# Print the account address to the user
print("Please only send testnet ETH to this account:", account.address)
qr = pyqrcode.create(account.address)
print(qr.terminal(quiet_zone=2))

print("Ropsten Testnet Faucet:", "https://faucet.metamask.io/")
print()

# Encrypt the key with a good passphrase!
keystore = account.encrypt(getpass.getpass("Please encrypt your keystore file with a password "))
print()

# Save the encrypted key to a local keystore file
with open('.your.keys', 'w') as f:
    f.write(json.dumps(keystore))
print("Saved keystore to ./.your.keys!")
print()
