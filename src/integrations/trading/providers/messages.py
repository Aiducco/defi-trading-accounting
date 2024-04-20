import dataclasses
import datetime
import typing

from src import enums as src_enums


@dataclasses.dataclass
class Order(object):
    order_id: str
    market: str
    type: src_enums.TradeType
    side: src_enums.TradeSide
    status: src_enums.TradeStatus
    size: float
    original_size: float
    created_at: int


@dataclasses.dataclass
class OrderFill(object):
    order_id: str
    market: str
    side: src_enums.TradeSide
    direction: typing.Optional[src_enums.TradeDirection]
    price: float
    size: float
    fee: float
    closed_pnl: typing.Optional[float]
    hash: typing.Optional[str]
    created_at: int


@dataclasses.dataclass
class OrderFillImportData(object):
    order_id: str
    market: str
    side: src_enums.TradeSide
    position_side: typing.Optional[src_enums.PositionSide]
    direction: typing.Optional[src_enums.TradeDirection]
    price: float
    size: float
    fee: float
    closed_pnl: float
    hash: typing.Optional[str]
    created_at: float


@dataclasses.dataclass
class Position(object):
    market: str
    status: src_enums.PositionStatus
    side: src_enums.PositionSide
    size: float
    remaining_size: float
    unrealized_pnl: float
    realized_pnl: float
    value: float
    created_at: float
    closed_at: typing.Optional[float]


@dataclasses.dataclass
class OrderHistory(object):
    wallet_address: str
    provider_name: str
    market: str
    order_id: int
    trade_side: str
    trade_type: str
    trade_status: str
    price: float
    size: float
    fee: float
    pnl: float
    created_at: str

    def to_list(self) -> typing.List:
        return [getattr(self, field.name) for field in dataclasses.fields(OrderHistory)]


@dataclasses.dataclass
class PositionFunding(object):
    market: str
    payment: float
    funding_rate: float
    position_size: float
    hash: typing.Optional[str]
    created_at: float


@dataclasses.dataclass
class PositionFundingHistory(object):
    wallet_address: str
    provider_name: str
    market: str
    amount_paid: str
    funding_rate: str
    position_size: str
    hash: str
    created_at: int

    def to_list(self) -> typing.List:
        return [
            getattr(self, field.name)
            for field in dataclasses.fields(PositionFundingHistory)
        ]


@dataclasses.dataclass
class WalletAccount(object):
    equity_value: float
