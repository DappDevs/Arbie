import click
import vyper

from eth_dev import DeveloperAccount


@click.command()
@click.option('--name',
        type=str,
        prompt=True,
        help="Something to describe the token")
@click.option('--symbol',
        type=str,
        prompt=True,
        help="Pick a short identifier, 3-4 letters long (all caps suggested)")
@click.option('--decimals',
        type=click.IntRange(0, 18),
        default=0,
        help="Adjust the number of decimal places to display (Default is zero)")
@click.option('--initial-supply',
        type=click.IntRange(0, 2**256-1),
        default=10**6,
        help="Adjust the initial supply (Default is 1m)")
def deploy_token(name, symbol, decimals, initial_supply):
    """
    Deploy and ERC20 token (written in Vyper!) to the test network

    NOTE: Do not add personally identifiable information, as it can not be erased!
    """

    # Compile the token
    with open('Token.vy', 'r') as f:
        token_interface = vyper.compile_code(
                f.read(),
                output_formats=['abi', 'bytecode', 'bytecode_runtime'],
            )

    # Load developer account
    dev = DeveloperAccount('./.your.keys')

    # Deploy with argument choices
    if click.confirm("Do you want to deploy the {0} token ({1})?".format(symbol, name)):
        print(dev.w3.eth.blockNumber)
        txn_hash = dev.w3.eth.contract(**token_interface).constructor(
                name.encode('utf-8'),
                symbol.encode('utf-8'),
                decimals,
                initial_supply,
            ).transact({'from':dev.address})
        click.echo('Deploying token... (https://ropsten.etherscan.io/tx/{})'.format(txn_hash.hex()))

        token_address = dev.w3.eth.waitForTransactionReceipt(txn_hash)['contractAddress']
        click.echo('Token Deployed! (https://ropsten.etherscan.io/token/{})'.format(token_address))

if __name__ == '__main__':
    deploy_token()
