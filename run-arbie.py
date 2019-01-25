import click
import time
from decimal import Decimal
from math import sqrt

from eth_dev import DeveloperAccount
from vypercoin import interface as erc20_interface

import uniswap


class Arbie(DeveloperAccount):
    def __init__(self, er=0.03):
        # Load developer account
        super().__init__('./.your.keys')

        # Expected return
        self.expected_return = er

        # Uniswap factory (central market lookup)
        self.factory = self.w3.eth.contract(
                uniswap.factory_address['ropsten'],
                **uniswap.factory_interface,
            )

        # Store all exchanges created for all the tokens we're tracking
        self.tokens = {}
        self.exchanges = {}

        # Filter to check for new exchanges
        self.new_exchange_filter = self.factory.events.NewExchange.createFilter(fromBlock=0)

        # Add all the current exchanges and tokens on Uniswap
        for log in self.new_exchange_filter.get_all_entries():
            self.add_exchange(log.args.token, log.args.exchange)

    def balance(self, ticker, owner):
        if ticker == 'ETH':
            return self.w3.fromWei(self.w3.eth.getBalance(owner.address), 'ether')
        else:
            return Decimal(self.tokens[ticker].functions.balanceOf(owner.address).call())

    def add_exchange(self, token_address, exchange_address):
        token = self.w3.eth.contract(token_address, **erc20_interface)
        exchange = self.w3.eth.contract(exchange_address, **uniswap.exchange_interface)
        try:
            ticker = token.functions.symbol().call().decode('ASCII')
        except:
            click.echo("(Setup)  Bad ticker: {}".format(token.address))
            return  # Abort!
        if ticker in self.tokens.keys():
            click.echo("(Setup)  Duplicate token: {} ({})".format(ticker, token.address))
            return  # Abort!
        if self.w3.eth.getBalance(exchange.address) < self.w3.toWei(1, 'ether'):
            click.echo("(Setup)  Not enough liquidity: {}".format(ticker))
            return  # Abort!
        if token.functions.balanceOf(self.address).call() == 0:
            click.echo("(Setup)  No Balance: {}".format(ticker))
            return  # Abort!
        self.tokens[ticker] = token
        self.exchanges[ticker] = exchange
        click.echo("(Setup)  Added token: {} ({})".format(ticker, token.address))

    def check_allowance(self, ticker, amount):
        token = self.tokens[ticker]
        exchange = self.exchanges[ticker]
        # Don't forget to approve the Exchange to move tokens on our behalf
        if token.functions.allowance(self.address, exchange.address).call() < amount:
            if not click.confirm("(Setup)  Approving {} [Tokens] for exchange".format(amount)):
                return  # Abort!
            txn_hash = token.functions.approve(
                    exchange.address,
                    amount,
                ).transact({'from':self.address})
            self.w3.eth.waitForTransactionReceipt(txn_hash)  # Wait...
            click.echo("\thttps://ropsten.etherscan.io/tx/{}".format(txn_hash.hex()))

    def get_price_and_supply(self, ticker):
        exchange = self.exchanges[ticker]
        eth_supply = self.balance('ETH', exchange)
        token_supply = self.balance(ticker, exchange)
        current_price = token_supply / eth_supply
        return current_price, eth_supply, token_supply

    def buy(self, ticker, min_tokens_to_buy, max_eth_to_sell):
        exchange = self.exchanges[ticker]
        ether_to_sell = exchange.functions.getEthToTokenOutputPrice(min_tokens_to_buy).call()
        assert ether_to_sell <= self.w3.toWei(max_eth_to_sell, 'ether'), "Not enough ETH!"
        click.echo("({})\tBuy {:0.3f} [Tokens] ({:0.2f}%), Sell {:0.3f} [ETH] ({:0.2f}%)".format(
                ticker,
                min_tokens_to_buy,
                100 * min_tokens_to_buy / self.balance(ticker, exchange),
                self.w3.fromWei(ether_to_sell, 'ether'),
                100 * self.w3.fromWei(ether_to_sell, 'ether') / self.balance('ETH', exchange),
            ))
        txn_hash = exchange.functions.ethToTokenSwapInput(
                min_tokens_to_buy,
                int(time.time()) + 60 * 2,  # deadline (2 mins from now)
            ).transact({'from': self.address, 'value': ether_to_sell})
        click.echo("\thttps://ropsten.etherscan.io/tx/{}".format(txn_hash.hex()))
        receipt = self.w3.eth.waitForTransactionReceipt(txn_hash)  # Wait...
        if receipt.status == 1:
            return self.w3.fromWei(ether_to_sell, 'ether')
        else:
            return Decimal(0)

    def sell(self, ticker, min_eth_to_buy, max_tokens_to_sell):
        exchange = self.exchanges[ticker]
        tokens_to_sell = exchange.functions.getTokenToEthOutputPrice(
                self.w3.toWei(min_eth_to_buy, 'ether')
            ).call()
        assert tokens_to_sell <= max_tokens_to_sell, "Not enough tokens!"
        click.echo("({})\tBuy {:0.3f} [ETH] ({:0.2f}%), Sell {:0.3f} [Tokens] ({:0.2f}%)".format(
                ticker,
                min_eth_to_buy,
                100 * min_eth_to_buy / self.balance('ETH', exchange),
                tokens_to_sell,
                100 * tokens_to_sell / self.balance(ticker, exchange),
            ))
        txn_hash = exchange.functions.tokenToEthSwapInput(
                tokens_to_sell,
                self.w3.toWei(min_eth_to_buy, 'ether'),
                int(time.time()) + 60 * 2,  # deadline (2 mins from now)
            ).transact({'from': self.address})
        click.echo("\thttps://ropsten.etherscan.io/tx/{}".format(txn_hash.hex()))
        receipt = self.w3.eth.waitForTransactionReceipt(txn_hash)  # Wait...
        if receipt.status == 1:
            return tokens_to_sell
        else:
            return Decimal(0)

    def maintain_price(self, ticker, target_price, max_tokens, max_ether):
        fee_percent = 0.003
        fee_mult = Decimal(1 + fee_percent)
        while True:
            current_price, eth_supply, token_supply = self.get_price_and_supply(ticker)
            click.echo("({})\tCurrent Price: {:0.3f} [Tokens/ETH]".format(ticker, current_price))
            if abs(target_price - current_price) < fee_percent * target_price:
                # Current price is within 'fee_percent' of target
                click.echo("({})\tNo Price Action...".format(ticker))
            elif target_price < current_price:  # Buy!
                min_tokens_to_buy = \
                    int((1 - sqrt(target_price / current_price)) * float(token_supply / fee_mult))
                assert Decimal(0.05) * token_supply > min_tokens_to_buy > 0, \
                        "{} is too much!".format(min_tokens_to_buy)
                max_ether -= self.buy(ticker, min_tokens_to_buy, max_ether)
            elif target_price > current_price:  # Sell!
                min_eth_to_buy = \
                    Decimal((1 - sqrt(current_price / target_price)) * float(eth_supply / fee_mult))
                assert Decimal(0.05) * eth_supply > min_eth_to_buy > 0, \
                        "{} is too much!".format(min_eth_to_buy)
                max_tokens -= self.sell(ticker, min_eth_to_buy, max_tokens)
            if max_tokens == 0 or max_ether == 0:
                click.echo("({})\tRan out of money!".format(ticker))
                break
            time.sleep(15)  # Wait for the next block...

    def trade(self):
        for ticker, exchange in self.exchanges.items():
            liquidity = self.balance('ETH', exchange)
            exchange_supply = self.balance(ticker, exchange)
            price = exchange_supply / liquidity
            click.echo("({})\tLiquidity: {:0.3f} [ETH]".format(ticker, liquidity))
            click.echo("({})\tPrice: {:0.3f} [Tokens/ETH]".format(ticker, price))
            click.echo("({})\tBalance: {:0.3f} [Tokens]".format(ticker, self.balance(ticker, self)))

            personal_supply = self.balance(ticker, self)
            trade_supply = int(Decimal(0.05) * (
                    exchange_supply if exchange_supply < personal_supply else personal_supply
                ))
            self.check_allowance(ticker, 2*trade_supply)
            price = 8000 # DEBUG
            self.maintain_price(ticker, price, trade_supply, Decimal(trade_supply / price))


@click.command()
@click.option('--expected-return',
        type=click.FloatRange(0.01, 0.05),
        default=0.03,
        help="Expected Return (in percent)")
def run_arbie(expected_return):
    """
    Run Arbie the arbitration bot!

    Looks at the uniswap exchange across all token markets,
    and identifies market oppurtunities that exist where it
    can increase the share of ETH in your account.

    WARNING! Arbie implements a terrible strategy!
             YOU WILL LOSE YOUR MONEY TO OTHER BOTS!
    """
    Arbie(er=expected_return).trade()

if __name__ == '__main__':
    run_arbie()
