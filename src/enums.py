import enum
import typing


class TradingProvider(enum.Enum):
    HYPERLIQUID = 1
    DYDX = 2


class TradeSide(enum.Enum):
    BUY = 1
    SELL = 2


class TradeType(enum.Enum):
    MARKET = 1
    STOP_MARKET = 2
    LIMIT = 3
    TRAILING_STOP = 4
    STOP = 5
    TAKE_PROFIT = 6


class TradeStatus(enum.Enum):
    PENDING = 1
    OPEN = 2
    FILLED = 3
    CANCELLED = 4
    UNTRIGGERED = 5


class TradeAccountantGroupBy(enum.Enum):
    DAILY = 1
    MONTHLY = 2


class PositionStatus(enum.Enum):
    OPEN = 1
    NEUTRAL = 2
    CLOSED = 3
    LIQUIDATED = 4


class PositionSide(enum.Enum):
    LONG = 1
    SHORT = 2
    NEUTRAL = 3


class TradeDirection(enum.Enum):
    OPEN_LONG = 1
    OPEN_SHORT = 2
    CLOSE_LONG = 3
    CLOSE_SHORT = 4

    @staticmethod
    def from_order_side_and_position_side(
        order_side: TradeSide, position_side: PositionSide
    ) -> typing.Optional["TradeDirection"]:
        return {
            (TradeSide.SELL, PositionSide.LONG): TradeDirection.CLOSE_LONG,
            (TradeSide.SELL, PositionSide.SHORT): TradeDirection.CLOSE_SHORT,
            (TradeSide.BUY, PositionSide.LONG): TradeDirection.OPEN_LONG,
            (TradeSide.BUY, PositionSide.SHORT): TradeDirection.OPEN_SHORT,
        }.get((order_side, position_side))


class TaoshiMiner(enum.Enum):
    TARVIS = 1
    TIMELESS = 2