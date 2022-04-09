from typing import List
from amm import Pool
from utils.fetcher import fetch_raw_data
from subprocess import Popen, PIPE


def get_account_sequence(account):
    """Fetch the account sequence from blockchain an returns it"""
    url = f"https://osmosis.stakesystems.io/auth/accounts/{account}"
    raw_data = fetch_raw_data(url)
    sequence = raw_data["result"]["value"]["sequence"]
    return sequence


def build_swap_command(transaction, amount_in, sequence, fees) -> str:
    """Builds the command to send to the blockchain"""
    denom_in = transaction.pools[0].asset_1.denom
    min_amount_out = amount_in

    base = "osmosisd tx gamm swap-exact-amount-in "

    if sequence:
        tail = f"--from=arbitrage --keyring-backend test --chain-id=osmosis-1 --fees={fees}uosmo" \
               f" --gas auto --gas-adjustment 1.2 --sequence={sequence} -y"
    else:
        tail = f"--from=arbitrage --keyring-backend test --chain-id=osmosis-1 --fees={fees}uosmo" \
               f" --gas auto --gas-adjustment 1.2 -y"

    initial = f"{amount_in}{denom_in} {min_amount_out} "

    # Add each route
    var = ""
    for pool in transaction.pools:
        pool_id = pool.idx
        denom_out = pool.asset_2.denom
        var += f"--swap-route-pool-ids={pool_id} --swap-route-denoms={denom_out} "

    # Assemble cmd line
    cmd = base + initial + var + tail
    return cmd


def send_cmd(cmd):
    p = Popen(cmd.split(" "), stdin=PIPE, stdout=PIPE)
    stdout = p.stdout.read().decode()
    if 'txhash' in stdout:
        hash = stdout.split("txhash: ")[1].split("\n")[0]
    else:
        hash = None
    return hash, stdout
