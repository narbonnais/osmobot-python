from amm.pool import Pool
import numpy as np
from typing import List
from amm.asset import Asset


class AMM:
    def __init__(self, name: str, pools: List[Pool]):
        self.name = name
        self.symbol_to_denom = {}  # asset_symbol --> asset_denom
        self.pools = {}   # pool_id  --> Pool
        self.graph = {}   # asset_source --> [  (pool_1, asset_symbol_dest_1) , (pool_2, asset_symbol_dest_2), ... ]
        self.num_assets = 0
        self.num_pools = 0

        for pool in pools:
            self.add_pool(pool)

    def add_asset(self, asset: Asset):
        if asset.symbol not in self.graph:
            self.graph[asset.symbol] = []
            self.num_assets += 1

        if asset.symbol not in self.symbol_to_denom:
            self.symbol_to_denom[asset.symbol] = asset.denom

    def add_pool(self, pool: Pool):
        if pool.idx not in self.graph:
            self.pools[pool.idx] = pool
            self.num_pools += 1

        asset_1 = pool.complete_asset_1
        asset_2 = pool.complete_asset_2

        self.add_asset(asset_1)
        self.add_asset(asset_2)

        self.graph[asset_1.symbol].append((pool, asset_2.symbol))
        self.graph[asset_2.symbol].append((pool, asset_1.symbol))

    def compute_cycle(self, cycle: List[str]) -> (float, List[Pool]):
        """
        Compute the cycle maximum change rate for the given cycle
        return :
           - change:         Cycle best change rate
           - list_of_pools:  list of pools to get the best change rate
        """

        if cycle[-1] != cycle[0]:
            cycle = cycle + [cycle[0]]

        change = 0
        pools = []

        for start, end in zip(cycle[:-1], cycle[1:]):
            available_pools = [link[0] for link in self.graph[start] if link[1] == end]

            max_change = -np.inf
            best_pool = None

            for pool in available_pools:
                pool.set_source(start)

                # If the change rate is better in this pool
                if pool.change > max_change:
                    best_pool = pool
                    max_change = pool.change

            change += max_change
            pools.append(best_pool)
        return change, pools
