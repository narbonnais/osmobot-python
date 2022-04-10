import os
import json
import attr
from typing import List, Dict

from amm import *
from utils import fetch_raw_data
import requests

script_dir = os.path.dirname(__file__)


@attr.s
class AstroportAmounts:
    token0_addr: str = attr.ib()
    token0_amount: int = attr.ib()
    token1_addr: str = attr.ib()
    token1_amount: int = attr.ib()
    pair_addr: str = attr.ib()

    @classmethod
    def from_data(cls, data, pair_addr):
        return cls(
            pair_addr=pair_addr,
            token0_addr=data["contractQuery"]["assets"][0]["info"]["token"]["contract_addr"] if "token" in data[
                "contractQuery"]["assets"][0]["info"] else data["contractQuery"]["assets"][0]["info"]["native_token"]["denom"],
            token0_amount=int(data["contractQuery"]["assets"][0]["amount"]),

            token1_addr=data["contractQuery"]["assets"][1]["info"]["token"]["contract_addr"] if "token" in data[
                "contractQuery"]["assets"][1]["info"] else data["contractQuery"]["assets"][1]["info"]["native_token"]["denom"],
            token1_amount=int(data["contractQuery"]["assets"][1]["amount"]),
        )


@attr.s
class AstroportToken:
    protocol: str = attr.ib()
    symbol: str = attr.ib()
    token: str = attr.ib()
    # icon = attr.ib()
    decimals: int = attr.ib()

    @classmethod
    def from_data(cls, data):
        return cls(
            protocol=data["protocol"],
            symbol=data["symbol"],
            token=data["token"],
            decimals=data["decimals"] if "decimals" in data else 6,
        )


@attr.s
class AstroportPair:
    pair_type: str = attr.ib()
    liquidity_token: str = attr.ib()
    contract_addr: str = attr.ib()
    token0_addr: str = attr.ib()
    token1_addr: str = attr.ib()

    @classmethod
    def from_data(cls, data):
        return cls(
            pair_type=list(data["pair_type"].keys())[0],
            liquidity_token=data["liquidity_token"],
            contract_addr=data["contract_addr"],
            token0_addr=list(
                list(data["asset_infos"][0].values())[0].values())[0],
            token1_addr=list(
                list(data["asset_infos"][1].values())[0].values())[0],
        )


@attr.s
class AstroportPool:
    pool_address: str = attr.ib()
    token_symbol: str = attr.ib()
    pool_liquidity: float = attr.ib(converter=float)
    volume_24h: float = attr.ib(converter=float)

    @classmethod
    def from_data(cls, data):
        return cls(
            pool_address=data["pool_address"],
            token_symbol=data["token_symbol"],
            pool_liquidity=data["pool_liquidity"],
            volume_24h=data["_24hr_volume"],
        )


def _build_query_amounts(pairs: List[AstroportPair]) -> str:
    """Build the graphql query"""
    def make_query(addr: str) -> str:
        return addr + ": wasm {contractQuery(contractAddress: \"" + addr + "\"query: {pool: { }})}"

    lst_queries = []
    for pair in pairs:
        addr = pair.contract_addr
        query = make_query(addr)
        lst_queries.append(query)

    return "{" + ",".join(lst_queries) + "}"


def fetch_astroport_pairs() -> List[AstroportPair]:
    """Read static local file of pairs and return list of pairs"""

    local_file = script_dir + "/../input_data/static/astroport/pairs.json"
    with open(local_file, "r") as f:
        raw_data = json.loads(f.read())

    lst_pairs = [AstroportPair.from_data(data) for data in raw_data["pairs"]]
    return lst_pairs


def fetch_astroport_amounts(pairs: List[AstroportPair]) -> Dict[str, AstroportAmounts]:
    url = "https://hive-terra.everstake.one/graphql"
    local_file = script_dir + "/../input_data/dynamic/astroport/amounts.json"
    data_raw = {"query": _build_query_amounts(pairs)}
    raw_data = requests.post(url, json=data_raw)
    raw_amounts = raw_data.json()
    with open(local_file, "w+") as f:
        f.write(json.dumps(raw_amounts, indent=4))

    dict_amounts = {pair_addr: AstroportAmounts.from_data(
        raw_amounts["data"][pair_addr], pair_addr) for pair_addr in raw_amounts["data"]}

    return dict_amounts


def fetch_pools(regenerate=True) -> List[Pool]:
    lst_pairs = fetch_astroport_pairs()
    dict_pairs = {pair.contract_addr: pair for pair in lst_pairs}
    dict_amounts = fetch_astroport_amounts(lst_pairs)

    pair_type_to_fee = {
        "xyk": 0.003,
        "stable": 0.0005,
    }

    pools = []
    for pair_addr, astroport_amount in dict_amounts.items():

        astroport_pair = dict_pairs[pair_addr]

        pair_type = astroport_pair.pair_type
        swap_fee = pair_type_to_fee[pair_type]

        asset_1 = Asset(symbol=astroport_amount.token0_addr, denom=astroport_amount.token0_addr)
        asset_2 = Asset(symbol=astroport_amount.token1_addr, denom=astroport_amount.token1_addr)

        amount_1 = astroport_amount.token0_amount
        amount_2 = astroport_amount.token1_amount

        if amount_1 == 0 or amount_2 == 0:
            continue

        pools.append(Pool(idx=pair_addr, asset_1=asset_1, asset_2=asset_2, swap_fee=swap_fee,
                          amount_in=amount_1, amount_out=amount_2, wi=1, wo=1, pool_type=pair_type))

        pools.append(Pool(idx=pair_addr, asset_1=asset_2, asset_2=asset_1, swap_fee=swap_fee,
                          amount_in=amount_2, amount_out=amount_1, wi=1, wo=1, pool_type=pair_type))

    return pools


def make_model(regenerate=True) -> AMM:
    """Create the model"""
    for attempt in range(10):
        try:
            pools = fetch_pools(regenerate=True)

            m_amm = AMM("terraswap", pools=pools)

            return m_amm
        except Exception as e:
            pass

    raise e


if __name__ == "__main__":
    m_amm = make_model(regenerate=True)
