from typing import List
from amm import AMM, Pool


def build_swap_command(dollars_delta, delta, from_asset, best_input, pools: List[Pool], cycle) -> str:

    for p, asset in zip(pools, cycle):
        p.set_source(asset)

    denom_in = pools[0].complete_asset_i.denom
    amount_in = min(int(best_input), 50_000_000)
    min_amount_out = amount_in
    fees = 2700

    sequence = " ".join([p.complete_asset_i.denom for p in pools])

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
