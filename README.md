# Osmosis python arbitrage bot

This bot gets data from osmosis liquidity pools and computes the best routes to perform arbitrage and make profit. It comes with a [discord bot](https://github.com/Alecsis/discord-bot) that can be used to monitor the bot's status and profits. 

## Quickstart

```sh
git clone https://github.com/Alecsis/osmobot-python
cd osmobot-python
source venv/bin/activate
pip3 install -r requirements.txt
python3 __main__.py
```

## Configuration

The configuration files are located in `config`:
- `starters.json`: defines the order of preference for the arbitrage routes. We need to define how much we can spend on each arbitrage (beware that OSMO amount decreases if we use a public validator).
- `config.json`: sets `do_transaction` to false only if you want to test the bot without actually sending any transaction.
