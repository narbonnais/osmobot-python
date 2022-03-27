from typing import List
import numpy as np
from amm.asset import Asset


class Pool:
    def __init__(self, idx: str, asset_1: Asset, asset_2: Asset, swap_fee: float):
        self.idx = idx
        self.swap_fee = swap_fee
        self.r = (1 - self.swap_fee)

        self.complete_asset_1 = asset_1
        self.complete_asset_2 = asset_2

        self.asset_1 = asset_1.symbol
        self.asset_2 = asset_2.symbol

        self.B1 = asset_1.amount
        self.B2 = asset_2.amount
        self.w1 = asset_1.weight
        self.w2 = asset_2.weight

        ## Change 1 --> 2 =  (B2/B1) * r * (w1/w2)

        self.change_from_1 = np.log(self.B2/self.B1) + np.log(self.w1/self.w2) + np.log(self.r)
        self.change_from_2 = np.log(self.B1/self.B2) + np.log(self.w2/self.w1) + np.log(self.r)

        self.from_asset = None
        self.to_asset = None
        self.i = None
        self.o = None
        self.change = None
        self.wi = None
        self.wo = None

        self.set_source(self.asset_1)

    def simulate_swap(self, from_asset, amount):
        Ai = amount

        self.set_source(from_asset)

        i = self.i
        o = self.o
        r = self.r
        wi = self.wi
        wo = self.wo
        to_asset = self.to_asset

        Ao = o * (1 - (i / (i + Ai * r)) ** (wi / wo))

        return to_asset, Ao

    def swap(self, from_asset, amount):

        to_asset, amount_out = self.simulate_swap(from_asset, amount)

        if from_asset == self.asset_1:
            self.B1 += amount
            self.B2 -= amount_out
        elif from_asset == self.asset_2:
            self.B2 += amount
            self.B1 -= amount_out
        else:
            raise Exception('Unknown asset')

    def set_source(self, from_asset):
        if from_asset == self.asset_1:
            self.from_asset = self.asset_1
            self.to_asset = self.asset_2
            self.i = self.B1
            self.o = self.B2
            self.wi = self.w1
            self.wo = self.w2
            self.change = self.change_from_1
        elif from_asset == self.asset_2:
            self.to_asset = self.asset_1
            self.from_asset = from_asset
            self.i = self.B2
            self.o = self.B1
            self.wi = self.w2
            self.wo = self.w1
            self.change = self.change_from_2
        else:
            raise Exception('Unknown asset')

    def __repr__(self):
        return f'{self.idx} {self.from_asset} =={np.round(self.change, 2)}==> {self.to_asset}'


def print_cycle(pools: List[Pool]):
    """ fonction pour afficher une suite de pools """
    res = ""
    for pool in pools:
        res += f"{pool.from_asset} =={pool.change}==> "
    res += pool.to_asset
    print(res)


def simulate_swaps(pools: List[Pool], from_asset: str, amount: float):
    for pool in pools:
        from_asset, amount = pool.simulate_swap(from_asset, amount)

    return from_asset, amount
