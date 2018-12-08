import json
import getpass

from eth_account import Account

# Create a branch new account with a random private key
account = Account.create(extra_entropy=getpass.getpass("Please smash the keyboard and press empty when ready :)"))

# Save the key to a local keystore file
keystore = account.encrypt(getpass.getpass("Please encrypt your keystore file with a password"))
with open('.your.keys', 'w') as f:
    f.write(json.dumps(keystore))
print("Saved keystore to ./.your.keys!")

# Communicate address to leader so they can give you ETH!
