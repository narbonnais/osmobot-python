from amm import Pool
from typing import List


def compute_amount_in(best_input, pools: List[Pool], cycle, starters, **kwargs):
    for p, asset in zip(pools, cycle):
        p.set_source(asset)

    symbol_in = pools[0].complete_asset_i.symbol

    m = starters[symbol_in]['maximum_input']

    # amount_in = np.round((m * best_input) / (m + best_input), 3)
    amount_in = min(m, best_input)

    return amount_in
