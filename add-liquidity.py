import click
import time

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
    Add liquidity to the Uniswap exchange for the given token

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
        if not click.confirm("No exchange for {}, create one?".format(token_address)):
            return  # Abort!
        exchange_address = factory.functions.createExchange(token_address).call()
        txn_hash = factory.functions.createExchange(token_address).transact({'from':dev.address})
        click.echo("Creating exchange... (https://ropsten.etherscan.io/tx/{})".format(txn_hash.hex()))
        dev.w3.eth.waitForTransactionReceipt(txn_hash)  # Just wait...
        assert exchange_address == factory.functions.getExchange(token_address).call(), \
                "There was an error with creating the exchange!"
        click.echo("Exchange created! (https://ropsten.etherscan.io/address/{})".format(exchange_address))

    # Now we can create our contract classes
    token = dev.w3.eth.contract(token_address, **token_interface)
    exchange = dev.w3.eth.contract(exchange_address, **uniswap.exchange_interface)

    # If the exchange has minted some liquidity tokens
    if exchange.functions.totalSupply().call() > 0:
        # Someone else has already provided liquidity, so the price is already set
        old_price = price
        price = token.functions.balanceOf(exchange.address).call() \
                / dev.w3.fromWei(dev.w3.eth.getBalance(exchange.address), 'ether')
        if old_price != price:
            click.echo("Exchange has liquidity, price was changed from {} to {} [Tokens/ETH]".format(old_price, price))

    # Then, calculate how much we're going to put into the pool
    tokens_to_deposit = int(percent_investment * token.functions.balanceOf(dev.address).call())
    ether_to_deposit = dev.w3.toWei(tokens_to_deposit / price, 'ether')  # 10**18 wei == 1 ether
    assert ether_to_deposit <= dev.w3.eth.getBalance(dev.address), \
            "You don't have {} [ETH]!".format(dev.w3.fromWei(ether_to_deposit, 'ether'))

    # Don't forget to approve the Exchange to move tokens on our behalf
    if token.functions.allowance(dev.address, exchange.address).call() < tokens_to_deposit:
        if not click.confirm("Approve {} [Tokens] for exchange?".format(tokens_to_deposit)):
            return  # Abort!
        txn_hash = token.functions.approve(exchange.address, tokens_to_deposit).transact({'from':dev.address})
        click.echo("Approving tokens for exchange... (https://ropsten.etherscan.io/tx/{})".format(txn_hash.hex()))
        dev.w3.eth.waitForTransactionReceipt(txn_hash)  # Wait here...
    click.echo("Allowance is {} [Tokens]".format(token.functions.allowance(dev.address, exchange.address).call()))

    # Finally, add liquidity (ETH + Tokens) to contract
    if not click.confirm("Deposit {1} [Tokens], {2} [ETH] (@ {0} [Tokens/ETH])?".format(
        price, tokens_to_deposit, dev.w3.fromWei(ether_to_deposit, 'ether')
    )):
        return  # Abort!
    txn_hash = exchange.functions.addLiquidity(
            int(ether_to_deposit * 0.90),  # min liquidity (Accept 10% fluctation)
            tokens_to_deposit,  # max tokens
            int(time.time()) + 60 * 2,  # deadline (2 mins from now)
            ).transact({'from': dev.address, 'value': ether_to_deposit})
    click.echo("Adding liquidity... (https://ropsten.etherscan.io/tx/{})".format(txn_hash.hex()))
    dev.w3.eth.waitForTransactionReceipt(txn_hash)  # Wait here...
    click.echo("Added liquidity!")

if __name__ == '__main__':
    add_liquidity()
