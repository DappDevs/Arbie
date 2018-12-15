import json

from flask import Flask, request
app = Flask(__name__)


with open('genesis.json', 'r') as f:
    genesis = json.loads(f.read())
# Make sure the accounts key is in there
if not genesis["accounts"]:
    genesis["accounts"] = {}


@app.route("/", methods=['POST'])
def new_account():
    address = request.form['address']
    # Give the account 100 Ether
    genesis["accounts"][address] = {"balance":hex(100*10**18)}
    # Write the genesis file for every update
    with open('genesis.json', 'w') as f:
        f.write(json.dumps(genesis))
    print("Added new account:", address)
    return address
