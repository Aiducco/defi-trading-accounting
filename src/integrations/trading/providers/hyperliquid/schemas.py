import typing

from marshmallow import EXCLUDE, Schema, fields, pre_load


# TODO: Add to common schemas and import here
class CommonSchema(Schema):
    class Meta:
        unknown = EXCLUDE


class OrderFill(CommonSchema):
    closedPnl = fields.Decimal(required=True, data_key="closedPnl")
    coin = fields.String(required=True, data_key="coin")
    crossed = fields.Boolean(required=True, data_key="crossed")
    dir = fields.String(required=True, data_key="dir")
    fee = fields.Decimal(required=True, data_key="fee")
    hash = fields.String(required=True, data_key="hash")
    oid = fields.Integer(required=True, data_key="oid")
    px = fields.Decimal(required=True, data_key="px")
    side = fields.String(required=True, data_key="side")
    startPosition = fields.Decimal(required=True, data_key="startPosition")
    sz = fields.Decimal(required=True, data_key="sz")
    time = fields.Integer(required=True, data_key="time")


class OrderFills(CommonSchema):
    order_fills = fields.Nested(OrderFill, many=True)


class Order(CommonSchema):
    coin = fields.String(required=True, data_key="coin")
    isPositionTpsl = fields.Boolean(required=True, data_key="isPositionTpsl")
    isTrigger = fields.Boolean(required=True, data_key="isTrigger")
    limitPx = fields.Decimal(required=True, data_key="limitPx")
    oid = fields.Integer(required=True, data_key="oid")
    orderType = fields.String(required=True, data_key="orderType")
    origSz = fields.Decimal(required=True, data_key="origSz")
    reduceOnly = fields.Boolean(required=True, data_key="reduceOnly")
    side = fields.String(required=True, data_key="side")
    sz = fields.Decimal(required=True, data_key="sz")
    timestamp = fields.Integer(required=True, data_key="timestamp")
    triggerCondition = fields.String(required=True, data_key="triggerCondition")
    triggerPx = fields.Decimal(required=True, data_key="triggerPx")
    status = fields.String(required=True, data_key="status")

    @pre_load
    def pre_process_data(self, data: typing.Dict, **kwargs: typing.Any) -> typing.Dict:
        data["order"]["order"]["status"] = data["order"]["status"]
        return data["order"]["order"]


class OpenOrder(CommonSchema):
    coin = fields.String(data_key="coin", required=True)
    limit_px = fields.String(data_key="limitPx", required=True)
    oid = fields.Integer(data_key="oid", required=True)
    orig_sz = fields.String(data_key="origSz", required=True)
    reduce_only = fields.Boolean(data_key="reduceOnly", required=True)
    side = fields.String(data_key="side", required=True)
    sz = fields.String(data_key="sz", required=True)
    timestamp = fields.Integer(data_key="timestamp", required=True)


class OpenOrders(CommonSchema):
    open_orders = fields.Nested(OpenOrder, many=True)


class Position(CommonSchema):
    coin = fields.String(data_key="coin", required=True)
    margin_used = fields.String(data_key="marginUsed", required=True)
    max_leverage = fields.Integer(data_key="maxLeverage", required=True)
    position_value = fields.String(data_key="positionValue", required=True)
    return_on_equity = fields.String(data_key="returnOnEquity", required=True)
    szi = fields.String(data_key="szi", required=True)
    unrealized_pnl = fields.String(data_key="unrealizedPnl", required=True)

    @pre_load
    def pre_process_data(self, data: typing.Dict, **kwargs: typing.Any) -> typing.Dict:
        return data["position"]


class Positions(CommonSchema):
    positions = fields.Nested(Position, many=True)


class PositionFunding(CommonSchema):
    coin = fields.String(data_key="coin", required=True)
    funding_rate = fields.Float(data_key="fundingRate", required=True)
    position_size = fields.Float(data_key="szi", required=True)
    payment = fields.Float(data_key="usdc", required=True)
    hash = fields.String(data_key="hash", required=True)
    timestamp = fields.Integer(data_key="timestamp", required=True)

    @pre_load
    def pre_process_data(self, data: typing.Dict, **kwargs: typing.Any) -> typing.Dict:
        return {
            "hash": data.pop("hash"),
            "timestamp": data.pop("time"),
            **data["delta"],
        }


class PositionFundings(CommonSchema):
    position_fundings = fields.Nested(PositionFunding, many=True)


class AccountPortfolio(CommonSchema):
    equity_value = fields.Float(required=True, data_key="accountValue")
