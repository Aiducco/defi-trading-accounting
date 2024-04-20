import typing

from marshmallow import EXCLUDE, Schema, fields, pre_load


# TODO: Add to common schemas and import here
class CommonSchema(Schema):
    class Meta:
        unknown = EXCLUDE


class TradeExportQuerySchema(CommonSchema):
    wallet_address = fields.String(required=True, data_key="wallet_address")
    provider = fields.String(required=True, data_key="provider")
    from_date = fields.Date(required=True, data_key="from_date")
    to_date = fields.Date(required=True, data_key="to_date")


class PositionFundingExportQuerySchema(CommonSchema):
    wallet_address = fields.String(required=True, data_key="wallet_address")
    provider = fields.String(required=True, data_key="provider")
    from_date = fields.Date(required=True, data_key="from_date")
    to_date = fields.Date(required=True, data_key="to_date")


class WalletAddressDataSchema(CommonSchema):
    address = fields.String(required=True, data_key="address")
    provider = fields.String(required=True, data_key="provider")
