# This code parses date/times, so please
#
#     pip install python-dateutil
#
# To use this code, make sure you
#
#     import json
#
# and then, to convert JSON from a string, do
#
#     result = cosmostation_transaction_from_dict(json.loads(json_string))

from dataclasses import dataclass
from typing import Any, List, TypeVar, Callable, Type, cast
from enum import Enum
from datetime import datetime
import dateutil.parser


T = TypeVar("T")
EnumT = TypeVar("EnumT", bound=Enum)


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_bool(x: Any) -> bool:
    assert isinstance(x, bool)
    return x


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def to_enum(c: Type[EnumT], x: Any) -> EnumT:
    assert isinstance(x, c)
    return x.value


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def from_datetime(x: Any) -> datetime:
    return dateutil.parser.parse(x)


@dataclass
class PurpleAttribute:
    key: str
    value: str
    index: bool

    @staticmethod
    def from_dict(obj: Any) -> 'PurpleAttribute':
        assert isinstance(obj, dict)
        key = from_str(obj.get("key"))
        value = from_str(obj.get("value"))
        index = from_bool(obj.get("index"))
        return PurpleAttribute(key, value, index)

    def to_dict(self) -> dict:
        result: dict = {}
        result["key"] = from_str(self.key)
        result["value"] = from_str(self.value)
        result["index"] = from_bool(self.index)
        return result


class TypeEnum(Enum):
    COIN_RECEIVED = "coin_received"
    COIN_SPENT = "coin_spent"
    MESSAGE = "message"
    TOKEN_SWAPPED = "token_swapped"
    TRANSFER = "transfer"
    TX = "tx"


@dataclass
class DataEvent:
    type: TypeEnum
    attributes: List[PurpleAttribute]

    @staticmethod
    def from_dict(obj: Any) -> 'DataEvent':
        assert isinstance(obj, dict)
        type = TypeEnum(obj.get("type"))
        attributes = from_list(PurpleAttribute.from_dict, obj.get("attributes"))
        return DataEvent(type, attributes)

    def to_dict(self) -> dict:
        result: dict = {}
        result["type"] = to_enum(TypeEnum, self.type)
        result["attributes"] = from_list(lambda x: to_class(PurpleAttribute, x), self.attributes)
        return result


@dataclass
class FluffyAttribute:
    key: str
    value: str

    @staticmethod
    def from_dict(obj: Any) -> 'FluffyAttribute':
        assert isinstance(obj, dict)
        key = from_str(obj.get("key"))
        value = from_str(obj.get("value"))
        return FluffyAttribute(key, value)

    def to_dict(self) -> dict:
        result: dict = {}
        result["key"] = from_str(self.key)
        result["value"] = from_str(self.value)
        return result


@dataclass
class LogEvent:
    type: TypeEnum
    attributes: List[FluffyAttribute]

    @staticmethod
    def from_dict(obj: Any) -> 'LogEvent':
        assert isinstance(obj, dict)
        type = TypeEnum(obj.get("type"))
        attributes = from_list(FluffyAttribute.from_dict, obj.get("attributes"))
        return LogEvent(type, attributes)

    def to_dict(self) -> dict:
        result: dict = {}
        result["type"] = to_enum(TypeEnum, self.type)
        result["attributes"] = from_list(lambda x: to_class(FluffyAttribute, x), self.attributes)
        return result


@dataclass
class Log:
    msg_index: int
    log: str
    events: List[LogEvent]

    @staticmethod
    def from_dict(obj: Any) -> 'Log':
        assert isinstance(obj, dict)
        msg_index = from_int(obj.get("msg_index"))
        log = from_str(obj.get("log"))
        events = from_list(LogEvent.from_dict, obj.get("events"))
        return Log(msg_index, log, events)

    def to_dict(self) -> dict:
        result: dict = {}
        result["msg_index"] = from_int(self.msg_index)
        result["log"] = from_str(self.log)
        result["events"] = from_list(lambda x: to_class(LogEvent, x), self.events)
        return result


@dataclass
class Amount:
    denom: str
    amount: int

    @staticmethod
    def from_dict(obj: Any) -> 'Amount':
        assert isinstance(obj, dict)
        denom = from_str(obj.get("denom"))
        amount = int(from_str(obj.get("amount")))
        return Amount(denom, amount)

    def to_dict(self) -> dict:
        result: dict = {}
        result["denom"] = from_str(self.denom)
        result["amount"] = from_str(str(self.amount))
        return result


@dataclass
class Fee:
    amount: List[Amount]
    gas_limit: int
    payer: str
    granter: str

    @staticmethod
    def from_dict(obj: Any) -> 'Fee':
        assert isinstance(obj, dict)
        amount = from_list(Amount.from_dict, obj.get("amount"))
        gas_limit = int(from_str(obj.get("gas_limit")))
        payer = from_str(obj.get("payer"))
        granter = from_str(obj.get("granter"))
        return Fee(amount, gas_limit, payer, granter)

    def to_dict(self) -> dict:
        result: dict = {}
        result["amount"] = from_list(lambda x: to_class(Amount, x), self.amount)
        result["gas_limit"] = from_str(str(self.gas_limit))
        result["payer"] = from_str(self.payer)
        result["granter"] = from_str(self.granter)
        return result


@dataclass
class Single:
    mode: str

    @staticmethod
    def from_dict(obj: Any) -> 'Single':
        assert isinstance(obj, dict)
        mode = from_str(obj.get("mode"))
        return Single(mode)

    def to_dict(self) -> dict:
        result: dict = {}
        result["mode"] = from_str(self.mode)
        return result


@dataclass
class ModeInfo:
    single: Single

    @staticmethod
    def from_dict(obj: Any) -> 'ModeInfo':
        assert isinstance(obj, dict)
        single = Single.from_dict(obj.get("single"))
        return ModeInfo(single)

    def to_dict(self) -> dict:
        result: dict = {}
        result["single"] = to_class(Single, self.single)
        return result


@dataclass
class PublicKey:
    type: str
    key: str

    @staticmethod
    def from_dict(obj: Any) -> 'PublicKey':
        assert isinstance(obj, dict)
        type = from_str(obj.get("@type"))
        key = from_str(obj.get("key"))
        return PublicKey(type, key)

    def to_dict(self) -> dict:
        result: dict = {}
        result["@type"] = from_str(self.type)
        result["key"] = from_str(self.key)
        return result


@dataclass
class SignerInfo:
    public_key: PublicKey
    mode_info: ModeInfo
    sequence: int

    @staticmethod
    def from_dict(obj: Any) -> 'SignerInfo':
        assert isinstance(obj, dict)
        public_key = PublicKey.from_dict(obj.get("public_key"))
        mode_info = ModeInfo.from_dict(obj.get("mode_info"))
        sequence = int(from_str(obj.get("sequence")))
        return SignerInfo(public_key, mode_info, sequence)

    def to_dict(self) -> dict:
        result: dict = {}
        result["public_key"] = to_class(PublicKey, self.public_key)
        result["mode_info"] = to_class(ModeInfo, self.mode_info)
        result["sequence"] = from_str(str(self.sequence))
        return result


@dataclass
class AuthInfo:
    signer_infos: List[SignerInfo]
    fee: Fee

    @staticmethod
    def from_dict(obj: Any) -> 'AuthInfo':
        assert isinstance(obj, dict)
        signer_infos = from_list(SignerInfo.from_dict, obj.get("signer_infos"))
        fee = Fee.from_dict(obj.get("fee"))
        return AuthInfo(signer_infos, fee)

    def to_dict(self) -> dict:
        result: dict = {}
        result["signer_infos"] = from_list(lambda x: to_class(SignerInfo, x), self.signer_infos)
        result["fee"] = to_class(Fee, self.fee)
        return result


@dataclass
class Route:
    pool_id: int
    token_out_denom: str

    @staticmethod
    def from_dict(obj: Any) -> 'Route':
        assert isinstance(obj, dict)
        pool_id = int(from_str(obj.get("poolId")))
        token_out_denom = from_str(obj.get("tokenOutDenom"))
        return Route(pool_id, token_out_denom)

    def to_dict(self) -> dict:
        result: dict = {}
        result["poolId"] = from_str(str(self.pool_id))
        result["tokenOutDenom"] = from_str(self.token_out_denom)
        return result


@dataclass
class Message:
    type: str
    sender: str
    routes: List[Route]
    token_in: Amount
    token_out_min_amount: int

    @staticmethod
    def from_dict(obj: Any) -> 'Message':
        assert isinstance(obj, dict)
        type = from_str(obj.get("@type"))
        sender = from_str(obj.get("sender"))
        routes = from_list(Route.from_dict, obj.get("routes"))
        token_in = Amount.from_dict(obj.get("tokenIn"))
        token_out_min_amount = int(from_str(obj.get("tokenOutMinAmount")))
        return Message(type, sender, routes, token_in, token_out_min_amount)

    def to_dict(self) -> dict:
        result: dict = {}
        result["@type"] = from_str(self.type)
        result["sender"] = from_str(self.sender)
        result["routes"] = from_list(lambda x: to_class(Route, x), self.routes)
        result["tokenIn"] = to_class(Amount, self.token_in)
        result["tokenOutMinAmount"] = from_str(str(self.token_out_min_amount))
        return result


@dataclass
class Body:
    messages: List[Message]
    memo: str
    timeout_height: int
    extension_options: List[Any]
    non_critical_extension_options: List[Any]

    @staticmethod
    def from_dict(obj: Any) -> 'Body':
        assert isinstance(obj, dict)
        messages = from_list(Message.from_dict, obj.get("messages"))
        memo = from_str(obj.get("memo"))
        timeout_height = int(from_str(obj.get("timeout_height")))
        extension_options = from_list(lambda x: x, obj.get("extension_options"))
        non_critical_extension_options = from_list(lambda x: x, obj.get("non_critical_extension_options"))
        return Body(messages, memo, timeout_height, extension_options, non_critical_extension_options)

    def to_dict(self) -> dict:
        result: dict = {}
        result["messages"] = from_list(lambda x: to_class(Message, x), self.messages)
        result["memo"] = from_str(self.memo)
        result["timeout_height"] = from_str(str(self.timeout_height))
        result["extension_options"] = from_list(lambda x: x, self.extension_options)
        result["non_critical_extension_options"] = from_list(lambda x: x, self.non_critical_extension_options)
        return result


@dataclass
class Tx:
    type: str
    body: Body
    auth_info: AuthInfo
    signatures: List[str]

    @staticmethod
    def from_dict(obj: Any) -> 'Tx':
        assert isinstance(obj, dict)
        type = from_str(obj.get("@type"))
        body = Body.from_dict(obj.get("body"))
        auth_info = AuthInfo.from_dict(obj.get("auth_info"))
        signatures = from_list(from_str, obj.get("signatures"))
        return Tx(type, body, auth_info, signatures)

    def to_dict(self) -> dict:
        result: dict = {}
        result["@type"] = from_str(self.type)
        result["body"] = to_class(Body, self.body)
        result["auth_info"] = to_class(AuthInfo, self.auth_info)
        result["signatures"] = from_list(from_str, self.signatures)
        return result


@dataclass
class Data:
    height: int
    txhash: str
    codespace: str
    code: int
    data: str
    raw_log: str
    logs: List[Log]
    info: str
    gas_wanted: int
    gas_used: int
    tx: Tx
    timestamp: datetime
    events: List[DataEvent]

    @staticmethod
    def from_dict(obj: Any) -> 'Data':
        assert isinstance(obj, dict)
        height = int(from_str(obj.get("height")))
        txhash = from_str(obj.get("txhash"))
        codespace = from_str(obj.get("codespace"))
        code = from_int(obj.get("code"))
        data = from_str(obj.get("data"))
        raw_log = from_str(obj.get("raw_log"))
        logs = from_list(Log.from_dict, obj.get("logs"))
        info = from_str(obj.get("info"))
        gas_wanted = int(from_str(obj.get("gas_wanted")))
        gas_used = int(from_str(obj.get("gas_used")))
        tx = Tx.from_dict(obj.get("tx"))
        timestamp = from_datetime(obj.get("timestamp"))
        events = from_list(DataEvent.from_dict, obj.get("events"))
        return Data(height, txhash, codespace, code, data, raw_log, logs, info, gas_wanted, gas_used, tx, timestamp, events)

    def to_dict(self) -> dict:
        result: dict = {}
        result["height"] = from_str(str(self.height))
        result["txhash"] = from_str(self.txhash)
        result["codespace"] = from_str(self.codespace)
        result["code"] = from_int(self.code)
        result["data"] = from_str(self.data)
        result["raw_log"] = from_str(self.raw_log)
        result["logs"] = from_list(lambda x: to_class(Log, x), self.logs)
        result["info"] = from_str(self.info)
        result["gas_wanted"] = from_str(str(self.gas_wanted))
        result["gas_used"] = from_str(str(self.gas_used))
        result["tx"] = to_class(Tx, self.tx)
        result["timestamp"] = self.timestamp.isoformat()
        result["events"] = from_list(lambda x: to_class(DataEvent, x), self.events)
        return result


@dataclass
class Header:
    id: int
    chain_id: str
    block_id: int
    timestamp: datetime

    @staticmethod
    def from_dict(obj: Any) -> 'Header':
        assert isinstance(obj, dict)
        id = from_int(obj.get("id"))
        chain_id = from_str(obj.get("chain_id"))
        block_id = from_int(obj.get("block_id"))
        timestamp = from_datetime(obj.get("timestamp"))
        return Header(id, chain_id, block_id, timestamp)

    def to_dict(self) -> dict:
        result: dict = {}
        result["id"] = from_int(self.id)
        result["chain_id"] = from_str(self.chain_id)
        result["block_id"] = from_int(self.block_id)
        result["timestamp"] = self.timestamp.isoformat()
        return result


@dataclass
class CosmoStationTransactionDetailsAnswer:
    header: Header
    data: Data
    sequenceNumber:int

    def __init__(self, header, data) -> None:
        self.header = header
        self.data = data
        self.sequenceNumber=self.data.tx.auth_info.signer_infos[0].sequence if len(self.data.tx.auth_info.signer_infos) > 0 else 0

    @staticmethod
    def from_dict(obj: Any) -> 'CosmoStationTransactionDetailsAnswer':
        assert isinstance(obj, dict)
        header = Header.from_dict(obj.get("header"))
        data = Data.from_dict(obj.get("data"))
        return CosmoStationTransactionDetailsAnswer(header, data)

    def to_dict(self) -> dict:
        result: dict = {}
        result["header"] = to_class(Header, self.header)
        result["data"] = to_class(Data, self.data)
        return result
    
    @property
    def isSuccess(self):
        if self.data.raw_log.startswith("failed to execute message;"):
            return False
        return True

def cosmostation_transaction_from_dict(s: Any) -> CosmoStationTransactionDetailsAnswer:
    return CosmoStationTransactionDetailsAnswer.from_dict(s)


def cosmostation_transaction_to_dict(x: CosmoStationTransactionDetailsAnswer) -> Any:
    return to_class(CosmoStationTransactionDetailsAnswer, x)
