import argparse
import vyper

from eth_dev import DeveloperAccount


# Load developer account
dev = DeveloperAccount('./.your.keys')

# Ask for some stuff
ap = argparse.ArgumentParser()
ap.add_argument('name', type=str,
        help="Add your name, or something else to describe the token")
ap.add_argument('symbol', type=str,
        help="Pick a short identifier, 3-4 letters long (like your initials)")
ap.add_argument('--decimals', type=int, default=0,
        help="Adjust the number of decimal places to display (Default is zero)")
ap.add_argument('--initial-supply', type=int, default=int(10**6),
        help="Adjust the initial supply (Default is 1m)")
args = ap.parse_args()

assert 0 <= args.decimals < 18, """
    Initial Supply must be a postive integer less than 18
    """
assert 0 <= args.initial_supply < 2**256, """
    Initial Supply must be a postive integer less than 2^256-1
    """

# Compile the token
with open('Token.vy', 'r') as f:
    token_interface = vyper.compile_code(
            f.read(),
            output_formats=['abi', 'bytecode', 'bytecode_runtime'],
        )

# Deploy with argument choices
txn_hash = dev.w3.eth.contract(**token_interface).constructor(
        args.name.encode('utf-8'),  # Token Name
        args.symbol.encode('utf-8'),  # Ticker Symbol
        args.decimals,  # Decimals
        args.initial_supply,  # Initial Supply
    ).transact({'from':dev.address})
print('Deploying token! (https://ropsten.etherscan.io/tx/{})'.format(txn_hash.hex()))

token_address = dev.w3.eth.waitForTransactionReceipt(txn_hash)['contractAddress']
print('Token Deployed! (https://ropsten.etherscan.io/token/{})'.format(token_address))
