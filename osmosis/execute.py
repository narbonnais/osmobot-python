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


def build_swap_command(amount_in, pools: List[Pool], cycle, sequence, **kwargs) -> str:

    for p, asset in zip(pools, cycle):
        p.set_source(asset)

    denom_in = pools[0].complete_asset_i.denom
    min_amount_out = amount_in
    fees = 2700

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
    for pool in pools:
        pool_id = pool.idx
        denom_out = pool.complete_asset_o.denom
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
