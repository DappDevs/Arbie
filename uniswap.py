import json as _json

factory_address = {
    'ropsten': '0x9c83dCE8CA20E9aAF9D3efc003b2ea62aBC08351',
}

exchange_interface = {}
factory_interface = {}

with open('depends/uniswap-contracts/abi/uniswap_factory.json', 'r') as f:
    factory_interface['abi'] = _json.loads(f.read())

with open('depends/uniswap-contracts/abi/uniswap_exchange.json', 'r') as f:
    exchange_interface['abi'] = _json.loads(f.read())

with open('depends/uniswap-contracts/bytecode/factory.txt', 'r') as f:
    factory_interface['bytecode'] = f.read().strip()

with open('depends/uniswap-contracts/bytecode/exchange.txt', 'r') as f:
    exchange_interface['bytecode'] = f.read().strip()
