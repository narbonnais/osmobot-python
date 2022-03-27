from typing import List, Dict
import json
import attr
import os

from utils import fetch_raw_data
from amm import AMM, Pool, Asset

script_dir = os.path.dirname(__file__)


@attr.s
class LCDPoolAsset:
    token_denom: str = attr.ib()
    token_amount: int = attr.ib(default=0)
    weight: int = attr.ib(default=0)

    @classmethod
    def from_data(cls, data):
        return cls(
            token_denom=data['token']['denom'],
            token_amount=int(data['token']['amount']),
            weight=int(data['weight'])
        )


@attr.s
class LCDPool:
    address: str = attr.ib()
    id: str = attr.ib()
    swap_fee: float = attr.ib(default=0)
    assets: List[LCDPoolAsset] = attr.ib(default=attr.Factory(list))
    total_weight: int = attr.ib(default=0)

    @classmethod
    def from_data(cls, data):
        return cls(
            address=data['address'],
            id=data['id'],
            swap_fee=float(data['poolParams']['swapFee']),
            assets=[LCDPoolAsset.from_data(asset)
                    for asset in data['poolAssets']],
            total_weight=int(data['totalWeight'])
        )


def get_pool_data_from_blockchain(regenerate) -> List[Pool]:
    """Read input_data from API, returns pools input_data"""

    local_file = os.path.join(script_dir, "../input_data/dynamic/osmosis/lcd_data.json")
    pools_url = "https://lcd-osmosis.keplr.app/osmosis/gamm/v1beta1/pools?pagination.limit=750"

    # Fetch and store input_data
    pools_data = fetch_raw_data(pools_url)
    os.makedirs(os.path.split(local_file)[0], exist_ok=True)
    with open(local_file, "w+") as f:
        f.write(json.dumps(pools_data, indent=4))

    denom_to_symbol = get_pool_additional_details(regenerate)

    # Parse input_data
    pools: List[Pool] = []

    for pool_data in pools_data['pools']:
        lcd_pool = LCDPool.from_data(pool_data)

        lcd_asset_1 = lcd_pool.assets[0]
        lcd_asset_2 = lcd_pool.assets[1]

        symbol_1 = denom_to_symbol[lcd_asset_1.token_denom]
        symbol_2 = denom_to_symbol[lcd_asset_2.token_denom]

        # TODO : Improve these dirty filters

        if symbol_1 == '' or symbol_2 == '':
            continue

        if lcd_asset_1.token_amount + lcd_asset_2.token_amount < 1e10 or \
                lcd_asset_1.token_amount + lcd_asset_2.token_amount > 1e21:
            continue

        asset_1 = Asset(symbol=denom_to_symbol[lcd_asset_1.token_denom], denom=lcd_asset_1.token_denom,
                        amount=lcd_asset_1.token_amount, weight=lcd_asset_1.weight, decimals=6)

        asset_2 = Asset(symbol=denom_to_symbol[lcd_asset_2.token_denom], denom=lcd_asset_2.token_denom,
                        amount=lcd_asset_2.token_amount, weight=lcd_asset_2.weight, decimals=6)

        pools.append(Pool(idx=lcd_pool.id, swap_fee=lcd_pool.swap_fee, asset_1=asset_1, asset_2=asset_2))

    return pools


def get_pool_additional_details(regenerate=True) -> Dict[str, str]:
    """Read input_data from API, returns pool details input_data"""

    # Fetch and store input_data
    local_file = script_dir + "/../input_data/dynamic/osmosis/denom_to_symbol.json"
    if regenerate:
        details_url = "https://api-osmosis.imperator.co/search/v1/pools"
        details_data = fetch_raw_data(details_url)
        denom_to_symbol: Dict[str, str] = {}
        for assets in details_data.values():
            for asset in assets:
                if asset['denom'] not in denom_to_symbol:
                    denom_to_symbol[asset['denom']] = asset['symbol']
        with open(local_file, "w+") as f:
            f.write(json.dumps(denom_to_symbol, indent=4))
    else:
        with open(local_file, "r") as f:
            denom_to_symbol = json.loads(f.read())

    return denom_to_symbol


def make_model(regenerate=True):
    """
    Takes raw and details input_data, then returns the AMM model
    :param regenerate forces the call of details API instead of reading from local file
    """

    pools = get_pool_data_from_blockchain(regenerate)

    m_amm = AMM("osmosis", pools=pools)

    return m_amm


if __name__ == "__main__":
    amm = make_model(regenerate=True)
