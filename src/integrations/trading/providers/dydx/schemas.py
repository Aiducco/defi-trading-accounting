import typing

from marshmallow import EXCLUDE, Schema, fields, pre_load


# TODO: Add to common schemas and import here
class CommonSchema(Schema):
    class Meta:
        unknown = EXCLUDE


class Order(CommonSchema):
    id = fields.Str(required=True, data_key="id")
    market = fields.Str(required=True, data_key="market")
    side = fields.Str(required=True, data_key="side")
    size = fields.Str(required=True, data_key="size")
    remaining_size = fields.Str(required=True, data_key="remainingSize")
    type = fields.Str(required=True, data_key="type")
    created_at = fields.DateTime(required=True, data_key="createdAt")
    status = fields.Str(required=True, data_key="status")


class AccountPortfolio(CommonSchema):
    equity_value = fields.Float(required=True, data_key="equity")


class Orders(CommonSchema):
    orders = fields.Nested(Order, many=True)


class Position(CommonSchema):
    market = fields.Str(required=True)
    status = fields.Str(required=True)
    side = fields.Str(required=True)
    size = fields.Str(required=True)
    max_size = fields.Str(required=True, data_key="maxSize")
    entry_price = fields.Str(required=True, data_key="entryPrice")
    exit_price = fields.Str(required=True, data_key="exitPrice")
    unrealized_pnl = fields.Str(required=True, data_key="unrealizedPnl")
    realized_pnl = fields.Str(required=True, data_key="realizedPnl")
    created_at = fields.DateTime(
        format="%Y-%m-%dT%H:%M:%S.%fZ", required=True, data_key="createdAt"
    )
    closed_at = fields.DateTime(
        format="%Y-%m-%dT%H:%M:%S.%fZ", data_key="closedAt", missing=None
    )
    sum_open = fields.Str(required=True, data_key="sumOpen")
    sum_close = fields.Str(required=True, data_key="sumClose")
    net_funding = fields.Str(required=True, data_key="netFunding")


class Positions(CommonSchema):
    positions = fields.Nested(Position, many=True)


class OrderFill(CommonSchema):
    id = fields.Str(required=True)
    side = fields.Str(required=True)
    liquidity = fields.Str(required=True)
    type = fields.Str(required=True)
    market = fields.Str(required=True)
    price = fields.Str(required=True)
    size = fields.Str(required=True)
    fee = fields.Str(required=True)
    created_at = fields.DateTime(
        format="%Y-%m-%dT%H:%M:%S.%fZ", required=True, data_key="createdAt"
    )
    order_id = fields.Str(required=True, data_key="orderId")


class OrderFills(CommonSchema):
    order_fills = fields.Nested(OrderFill, many=True)


class PositionFunding(CommonSchema):
    market = fields.Str(required=True)
    payment = fields.Str(required=True)
    rate = fields.Str(required=True)
    position_size = fields.Str(data_key="positionSize", required=True)
    price = fields.Str(required=True)
    effective_at = fields.DateTime(
        format="%Y-%m-%dT%H:%M:%S.%fZ", required=True, data_key="effectiveAt"
    )


class PositionFundings(CommonSchema):
    position_fundings = fields.Nested(PositionFunding, many=True)


class Market(CommonSchema):
    oracle_price = fields.Float(required=True, data_key="oraclePrice")
