import attr


@attr.define
class Asset:
    symbol: str
    denom: str
    amount: int
    weight: int = 1
    decimals: int = 6
