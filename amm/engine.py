import numpy as np
from typing import List
import scipy.optimize
from amm import Transaction, Pool


def simulate_swaps(pools: List[Pool], amount: float):
    for pool in pools:
        amount = pool.simulate_swap(amount)
    return amount


def find_optimal_amount(pools: List[Pool], xatol=10000, fatol=100):

    if all([p.wi == p.wo for p in pools]):
        p1 = pools[0]

        i_eq = p1.i
        o_eq = p1.o

        for i in range(1, len(pools)):
            pool = pools[i]

            i_eq = (i_eq * pool.i) / (pool.i + pool.r * o_eq)
            o_eq = (pool.r * o_eq * pool.o) / (pool.i + pool.r * o_eq)

        x_op = (np.sqrt(i_eq * o_eq * p1.r) - i_eq) / p1.r
        return x_op
    else:

        def delta(x):
            return x - simulate_swaps(pools, x)

        res = scipy.optimize.minimize(delta, np.array([0]), method='Nelder-Mead', options={'xatol': xatol,
                                                                                           'fatol': fatol})

        return float(res.x)


def find_transactions(cycle, amm, config, starters):
    transactions = []
    change = amm.compute_cycle(cycle)
    if change < 0:
        return transactions

    for pools in amm.all_pools_with_cycle(cycle):

        from_asset = cycle[0]
        best_input = find_optimal_amount(pools, xatol=config['xatol'], fatol=config['fatol'])

        if best_input <= 0:
            continue

        output = simulate_swaps(pools=pools, amount=best_input)

        delta = output - best_input

        dollars_delta = float(starters[from_asset]['current_price']) * delta

        if dollars_delta <= config['minimum_dollars_delta']:
            continue

        transaction = Transaction(dollars_delta=dollars_delta, delta=delta, pools=pools, cycle=cycle,
                                  from_asset=from_asset, best_input=best_input, change=change)

        transactions.append(transaction)

    return transactions
