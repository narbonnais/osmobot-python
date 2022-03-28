from amm.pool import Pool, simulate_swaps
import numpy as np
from typing import List
import scipy.optimize


def find_optimal_amount(pools: List[Pool], from_asset):

    if all([p.wi == p.wo for p in pools]):
        p1 = pools[0]
        p1.set_source(from_asset)
        to_asset = p1.to_asset

        i_eq = p1.i
        o_eq = p1.o

        for i in range(1, len(pools)):
            pool = pools[i]

            from_asset = to_asset
            pool.set_source(from_asset)
            to_asset = pool.to_asset

            i_eq = (i_eq * pool.i) / (pool.i + pool.r * o_eq)
            o_eq = (pool.r * o_eq * pool.o) / (pool.i + pool.r * o_eq)

        x_op = (np.sqrt(i_eq * o_eq * p1.r) - i_eq) / p1.r
        return x_op
    else:

        def delta(x):
            return x - simulate_swaps(pools, from_asset, x)[1]

        res = scipy.optimize.minimize(delta, np.array([0.01]), method='Nelder-Mead')

        return float(res.x)