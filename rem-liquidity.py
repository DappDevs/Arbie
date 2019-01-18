import click
import time

from eth_dev import DeveloperAccount
from vypercoin import interface as token_interface

import uniswap


@click.command()
@click.argument('token-address', type=str)
@click.option('--percent-liquidity',
        type=click.FloatRange(0.01, 1.00),
        default=0.20,
        help="Percentage of liquidity to withdraw.")
def rem_liquidity(token_address, percent_liquidity):
    """
    Withdraw liquidity to the Uniswap exchange for the given token
    """
    # Load developer account
    dev = DeveloperAccount('./.your.keys')

    # Token contract
    token = dev.w3.eth.contract(token_address, **token_interface)

    # Uniswap factory (central market lookup)
    factory = dev.w3.eth.contract(uniswap.factory_address['ropsten'], **uniswap.factory_interface)

    # Get exchange for token (if it exists!)
    exchange_address = factory.functions.getExchange(token_address).call()
    if exchange_address == '0x0000000000000000000000000000000000000000':
        return  # Abort!
    exchange = dev.w3.eth.contract(exchange_address, **uniswap.exchange_interface)

    # Then, calculate how much we're going to take out of the pool
    liquidity_to_withdraw = int(percent_liquidity * exchange.functions.balanceOf(dev.address).call())
    percent_of_total = (liquidity_to_withdraw / exchange.functions.totalSupply().call())
    tokens_to_withdraw = int(percent_of_total * token.functions.balanceOf(exchange.address).call())
    ether_to_withdraw = int(percent_of_total * dev.w3.eth.getBalance(exchange.address))
    price = (tokens_to_withdraw / dev.w3.fromWei(ether_to_withdraw, 'ether'))
    
    # Finally, remove liquidity (ETH + Tokens) from contract
    if not click.confirm("Withdraw {1} [Tokens], {2} [ETH] (@ {0} [Tokens/ETH])?".format(
        price, tokens_to_withdraw, dev.w3.fromWei(ether_to_withdraw, 'ether')
    )):
        return  # Abort!
    txn_hash = exchange.functions.removeLiquidity(
            liquidity_to_withdraw,  # amount of UNI to burn
            int(ether_to_withdraw * 0.90),  # min ether to accept (Accept 10% fluctation)
            int(tokens_to_withdraw * 0.90),  # min tokens to accept (Accept 10% fluctation)
            int(time.time()) + 60 * 2,  # deadline (2 mins from now)
        ).transact({'from': dev.address})
    click.echo("Removing liquidity... (https://ropsten.etherscan.io/tx/{})".format(txn_hash.hex()))
    dev.w3.eth.waitForTransactionReceipt(txn_hash)  # Wait here...
    click.echo("Removed liquidity!")

if __name__ == '__main__':
    rem_liquidity()
