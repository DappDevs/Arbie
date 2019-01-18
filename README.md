# Arbie: the friendly arbitration bot!

## Installation
1. Install Python 3.6+
   NOTE: Activate a new virtualenv!
2. Install dependancies `pip install -r requirements.txt`

## Demo
1. Generate a new account with `python new-account.py` and add testnet ETH
   NOTE: Don't upload `./.your.keys` because people can brute force your password!
2. Create a new token with `python create-token.py "[DESCRIPTION]" [TICKER SYMBOL]`
3. Create a Uniswap market and add liquidity using
   `python add-liquidity.py [TOKEN ADDRESS] [PERCENT INVESTMENT] [PRICE]`
4. Run your bot using `python run-arbie.py [EXPECTED RETURN]`
5. ...Profit!
