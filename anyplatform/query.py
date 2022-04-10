import os
import json
import attr
from typing import List

from amm import *
from utils import fetch_raw_data
import random
import string

script_dir = os.path.dirname(__file__)


def fetch_pools(regenerate=True) -> List[Pool]:

    pools = []
    for _ in range(10):

        amount_token0 = random.randint(1, 100)
        amount_token1 = random.randint(1, 100)

        # random string with 3 chars
        symbol_token0 = random.choices(list(string.ascii_lowercase), k=3)
        symbol_token1 = random.choices(list(string.ascii_lowercase), k=3)

        pool_idx = str(random.randint(0, 1000))

        if amount_token0 < 1 or amount_token1 < 1:
            continue

        asset_1 = Asset(symbol=symbol_token0, denom=symbol_token0)
        asset_2 = Asset(symbol=symbol_token1, denom=symbol_token1)

        pools.append(Pool(idx=pool_idx, asset_1=asset_1, asset_2=asset_2, swap_fee=0.003,
                          amount_in=amount_token0, amount_out=amount_token1, wi=1, wo=1))

        pools.append(Pool(idx=pool_idx, asset_1=asset_2, asset_2=asset_1, swap_fee=0.003,
                          amount_in=amount_token1, amount_out=amount_token0, wi=1, wo=1))

    return pools


def make_model(regenerate=True) -> AMM:
    """
    :param regenerate: regenerate denom_to_symbol
    :return: amm
    """
    pools = fetch_pools(regenerate=regenerate)

    for attempt in range(10):
        try:

            m_amm = AMM("anyplatform", pools=pools)

            return m_amm
        except Exception as e:
            pass
    raise e


if __name__ == "__main__":
    m_amm = make_model(regenerate=True)
