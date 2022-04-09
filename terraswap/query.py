import os
import json
import attr
from typing import List

from amm import *
from utils import fetch_raw_data

script_dir = os.path.dirname(__file__)
blockchain_prefix = "terra"


@attr.s
class DashboardPair:
    timestamp: str = attr.ib()
    pairAddress: str = attr.ib()
    token0: str = attr.ib()
    token0Volume: int = attr.ib()
    token0Reserve: int = attr.ib()
    token1: str = attr.ib()
    token1Volume: int = attr.ib()
    token1Reserve: int = attr.ib()
    totalLpTokenShare: int = attr.ib()
    volumeUst: int = attr.ib()
    liquidityUst: int = attr.ib()
    token0Symbol: str = attr.ib()
    token0Decimals: int = attr.ib()
    token1Symbol: str = attr.ib()
    token1Decimals: int = attr.ib()
    apr: float = attr.ib()
    pairAlias: str = attr.ib()

    @classmethod
    def from_data(cls, data):
        return cls(
            timestamp=str(data['timestamp']),
            pairAddress=str(data['pairAddress']),
            token0=str(data['token0']),
            token0Volume=int(data['token0Volume']),
            token0Reserve=int(data['token0Reserve']),
            token1=str(data['token1']),
            token1Volume=int(data['token1Volume']),
            token1Reserve=int(data['token1Reserve']),
            totalLpTokenShare=int(data['totalLpTokenShare']),
            volumeUst=int(data['volumeUst']),
            liquidityUst=int(data['liquidityUst']),
            token0Symbol=str(data['token0Symbol']),
            token0Decimals=int(data['token0Decimals']),
            token1Symbol=str(data['token1Symbol']),
            token1Decimals=int(data['token1Decimals']),
            apr=float(data['apr']),
            pairAlias=str(data['pairAlias']),
        )


@attr.s
class TerraswapToken:
    name: str = attr.ib()
    symbol: str = attr.ib()
    decimals: int = attr.ib()
    contract_addr: str = attr.ib()
    total_supply: int = attr.ib()
    verified: bool = attr.ib()

    @classmethod
    def from_data(cls, data):
        name = data['name'] if 'name' in data else None
        symbol = data['symbol'] if 'symbol' in data else None
        decimals = data['decimals'] if 'decimals' in data else None
        contract_addr = data['contract_addr'] if 'contract_addr' in data else None
        total_supply = data['total_supply'] if 'total_supply' in data else None
        verified = data['verified'] if 'verified' in data else None
        return cls(
            name,
            symbol,
            decimals,
            contract_addr,
            total_supply,
            verified
        )


def fetch_terraswap_tokens(regenerate=True) -> List[TerraswapToken]:
    local_file = os.path.join(script_dir, "../input_data/dynamic/terraswap/denom_to_symbol.json")

    if regenerate:
        # Fetch API
        url = "https://api.terraswap.io/tokens"
        raw_data = fetch_raw_data(url)
        denom_to_symbol = {token['contract_addr']: token['symbol'] for token in raw_data}
        with open(local_file, 'w') as f:
            json.dump(denom_to_symbol, f, indent=4)
    else:
        with open(local_file, "r") as f:
            denom_to_symbol = json.loads(f.read())

    # Process data
    # lst_tokens: List[TerraswapToken] = [TerraswapToken.from_data(token_data) for token_data in raw_data]
    # lst_tokens: List[TerraswapToken] = [t for t in lst_tokens if t.decimals is not None]

    return denom_to_symbol


def fetch_terraswap_dashboard_pairs(regenerate=True) -> List[Pool]:
    local_file = os.path.join(script_dir, "../input_data/dynamic/terraswap/data.json")

    if regenerate:
        # Fetch API
        dashboard_pairs_url = "https://api.terraswap.io/dashboard/pairs"
        raw_data = fetch_raw_data(dashboard_pairs_url)
    else:
        with open(local_file, "r") as f:
            raw_data = json.loads(f.read())

    # Process data
    dashboard_pairs: List[DashboardPair] = [DashboardPair.from_data(pair_data) for pair_data in raw_data]

    # Save to local file
    with open(local_file, "w+") as f:
        f.write(json.dumps(raw_data, indent=4))

    pools = []
    for dashboard_pair in dashboard_pairs:

        if dashboard_pair.token0Volume == 0 or dashboard_pair.token1Volume == 0:
            continue

        asset_1 = Asset(symbol=dashboard_pair.token0Symbol, denom=dashboard_pair.token0)
        asset_2 = Asset(symbol=dashboard_pair.token1Symbol, denom=dashboard_pair.token1)

        pools.append(Pool(idx=dashboard_pair.pairAddress, asset_1=asset_1, asset_2=asset_2, swap_fee=0.003,
                          amount_in=dashboard_pair.token0Volume, amount_out=dashboard_pair.token1Volume, wi=1, wo=1))

        pools.append(Pool(idx=dashboard_pair.pairAddress, asset_1=asset_2, asset_2=asset_1, swap_fee=0.003,
                          amount_in=dashboard_pair.token1Volume, amount_out=dashboard_pair.token0Volume, wi=1, wo=1))

    return pools


def make_model(regenerate=True) -> AMM:
    tokens = fetch_terraswap_tokens(regenerate)

    for attempt in range(10):
        try:
            pools = fetch_terraswap_dashboard_pairs(regenerate=True)

            m_amm = AMM("terraswap", pools=pools)

            return m_amm
        except Exception as e:
            pass

    raise e


if __name__ == "__main__":
    m_amm = make_model(regenerate=True)
