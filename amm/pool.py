from typing import List
import numpy as np
from amm.asset import Asset


class Pool:
    """
    A pool of assets. It swaps asset1 --> asset2.
    """
    def __init__(self, idx: str, asset_1: Asset, asset_2: Asset, swap_fee: float, amount_in, amount_out, wi, wo,
                 pool_type='xyk'):

        self.idx = idx
        self.swap_fee = swap_fee
        self.r = (1 - self.swap_fee)

        self.asset_1 = asset_1
        self.asset_2 = asset_2

        self.symbol_1 = asset_1.symbol
        self.symbol_2 = asset_2.symbol

        self.i = amount_in
        self.o = amount_out
        self.wi = wi
        self.wo = wo

        self.pool_type = pool_type

        if pool_type == 'xyk':
            self.change = np.log(self.o / self.i) + np.log(self.wi / self.wo) + np.log(self.r)

        elif pool_type == 'stable':
            self.change = np.log(self.wi / self.wo) + np.log(self.r)

    def simulate_swap(self, amount):
        if self.pool_type == 'xyk':
            Ai = amount

            i = self.i
            o = self.o
            r = self.r
            wi = self.wi
            wo = self.wo

            Ao = o * (1 - (i / (i + Ai * r)) ** (wi / wo))

            return Ao

        elif self.pool_type == 'stable':
            Ai = amount
            Ao = min(self.o, Ai * self.wi / self.wo * self.r)
            return Ao

    def __repr__(self):
        return f'{self.idx} {self.symbol_1} =={np.round(self.change, 2)}==> {self.symbol_2}'


def print_cycle(pools: List[Pool]):
    """ fonction pour afficher une suite de pools """
    res = ""
    for pool in pools:
        res += f"{pool.symbol_1} =={pool.change}==> "
    res += pool.symbol_2
    print(res)
