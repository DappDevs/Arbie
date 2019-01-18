import click

from eth_dev import DeveloperAccount
from vypercoin import interface as token_interface

import uniswap


# NOTE With 1m Tokens, 20% invested (200k) at price of 10k Tokens/ETH
#      is 2 ETH liquidity. Therefore, everyone should have at least 2 ETH.

@click.command()
@click.argument('token-address', type=str)
@click.option('--percent-investment',
        type=click.FloatRange(0.01, 1.00),
        default=0.20,
        help="Percentage of token holdings to invest as market maker.")
@click.option('--price',
        type=click.IntRange(1e3, 1e6),
        default=10000,
        help="Price to set, tokens per ETH (if exchange not created). Ether balances must be GEQ price*tokens.")
def add_liquidity(token_address, percent_investment, price):
    """
    Add liquidity to the Uniswap exchcange for the given token

    NOTE Will create exchange if it doesn't exist!
    """
    # Load developer account
    dev = DeveloperAccount('./.your.keys')

    # Uniswap factory (central market lookup)
    factory = dev.w3.eth.contract(uniswap.factory_address['ropsten'], **uniswap.factory_interface)

    # Check if Uniswap has an exchange for token
    exchange_address = factory.functions.getExchange(token_address).call()
    if exchange_address == '0x0000000000000000000000000000000000000000':
        # No exchange, so create one!
        if click.confirm("No exchange for {}, create one?".format(token_address)):
            exchange_address = factory.functions.createExchange(token_address).call()
            txn_hash = factory.functions.createExchange(token_address).transact({'from':dev.address})
            click.echo("Creating exchange... (https://ropsten.etherscan.io/tx/{})".format(txn_hash.hex()))
            dev.w3.eth.waitForTransactionReceipt(txn_hash)  # Just wait...
            assert exchange_address == factory.functions.getExchange(token_address).call()
            click.echo("Exchange created! (https://ropsten.etherscan.io/address/{})".format(exchange_address))
        else:
            return  # Abort!

    # Now we can create our contract classes
    token = dev.w3.eth.contract(token_address, **token_interface)
    exchange = dev.w3.eth.contract(exchange_address, **uniswap.exchange_interface)

    # First, calculate how much we're going to put into the pool
    tokens_to_deposit = int(percent_investment * token.functions.balanceOf(dev.address).call())
    ether_to_deposit = dev.w3.toWei(tokens_to_deposit / price, 'ether')  # 10**18 wei == 1 ether
    assert ether_to_deposit <= dev.w3.eth.getBalance(dev.address), \
            "You don't have {} ETH!".format(dev.w3.fromWei(ether_to_deposit, 'ether'))
    click.echo("Depositing {1} Tokens, {2} ETH @ {0} ETH/Token".format(
            1/price, tokens_to_deposit, dev.w3.fromWei(ether_to_deposit, 'ether')
        ))

    # Don't forget to approve the Exchange to move tokens on our behalf


    # Finally, add liquidity (ETH + Tokens) to contract

if __name__ == '__main__':
    add_liquidity()
