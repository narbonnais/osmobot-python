# To use this code, make sure you
#
#     import json
#
# and then, to convert JSON from a string, do
#
#     result = cosmo_station_balance_answer_from_dict(json.loads(json_string))

from dataclasses import dataclass
from typing import Any, List, TypeVar, Callable, Type, cast


T = TypeVar("T")


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_none(x: Any) -> Any:
    assert x is None
    return x


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


@dataclass
class Balance:
    denom: str
    amount: int

    @staticmethod
    def from_dict(obj: Any) -> 'Balance':
        assert isinstance(obj, dict)
        denom = from_str(obj.get("denom"))
        amount = int(from_str(obj.get("amount")))
        return Balance(denom, amount)

    def to_dict(self) -> dict:
        result: dict = {}
        result["denom"] = from_str(self.denom)
        result["amount"] = from_str(str(self.amount))
        return result


@dataclass
class Pagination:
    next_key: None
    total: int

    @staticmethod
    def from_dict(obj: Any) -> 'Pagination':
        assert isinstance(obj, dict)
        next_key = from_none(obj.get("next_key"))
        total = int(from_str(obj.get("total")))
        return Pagination(next_key, total)

    def to_dict(self) -> dict:
        result: dict = {}
        result["next_key"] = from_none(self.next_key)
        result["total"] = from_str(str(self.total))
        return result


@dataclass
class CosmoStationBalanceAnswer:
    balances: List[Balance]
    pagination: Pagination

    @staticmethod
    def from_dict(obj: Any) -> 'CosmoStationBalanceAnswer':
        assert isinstance(obj, dict)
        balances = from_list(Balance.from_dict, obj.get("balances"))
        pagination = Pagination.from_dict(obj.get("pagination"))
        return CosmoStationBalanceAnswer(balances, pagination)

    def to_dict(self) -> dict:
        result: dict = {}
        result["balances"] = from_list(lambda x: to_class(Balance, x), self.balances)
        result["pagination"] = to_class(Pagination, self.pagination)
        return result
    



def cosmo_station_balance_answer_from_dict(s: Any) -> CosmoStationBalanceAnswer:
    return CosmoStationBalanceAnswer.from_dict(s)

def cosmo_station_balance_answer_to_dict(x: CosmoStationBalanceAnswer) -> Any:
    return to_class(CosmoStationBalanceAnswer, x)
