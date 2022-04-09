import attr


@attr.define
class Asset:
    symbol: str
    denom: str
