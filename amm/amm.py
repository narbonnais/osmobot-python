from amm.pool import Pool
import numpy as np
from typing import List
from amm.asset import Asset
import itertools


class AMM:
    def __init__(self, name: str, pools: List[Pool]):
        self.name = name
        self.symbol_to_denom = {}  # asset_symbol --> asset_denom
        self.pools = {}   # pool_id  --> Pool
        self.graph = {}   # asset_symbol --> [  (pool_1, asset_symbol_dest_1) , (pool_2, asset_symbol_dest_2), ... ]
        self.assets = {}  # asset_symbol --> Asset
        self.num_assets = 0
        self.num_pools = 0

        for pool in pools:
            self.add_pool(pool)

    def add_asset(self, asset: Asset):
        if asset.symbol not in self.graph:
            self.graph[asset.symbol] = []
            self.assets[asset.symbol] = asset
            self.num_assets += 1

        if asset.symbol not in self.symbol_to_denom:
            self.symbol_to_denom[asset.symbol] = asset.denom

    def add_pool(self, pool: Pool):
        if pool.idx not in self.graph:
            self.pools[pool.idx] = pool
            self.num_pools += 1

        symbol_1 = pool.symbol_1
        symbol_2 = pool.symbol_2

        self.add_asset(pool.asset_1)
        self.add_asset(pool.asset_2)

        self.graph[symbol_1].append((pool, symbol_2))

    def compute_cycle(self, cycle: List[str]) -> float:
        """
        Compute the cycle maximum change rate for the given cycle
        return :
           - change:         Cycle best change rate
        """

        if cycle[-1] != cycle[0]:
            cycle = cycle + [cycle[0]]

        change = 0

        for start, end in zip(cycle[:-1], cycle[1:]):
            available_pools = [link[0] for link in self.graph[start] if link[1] == end]

            max_change = -np.inf

            for pool in available_pools:
                # If the change rate is better in this pool
                if pool.change > max_change:
                    max_change = pool.change

            change += max_change
        return change

    def all_pools_with_cycle(self, cycle: List[str]) -> List[List[Pool]]:
        if cycle[-1] != cycle[0]:
            cycle = cycle + [cycle[0]]

        list_of_pools = []
        for start, end in zip(cycle[:-1], cycle[1:]):
            available_pools = [link[0] for link in self.graph[start] if link[1] == end]
            list_of_pools.append(available_pools)

        return list(map(list, itertools.product(*list_of_pools)))
