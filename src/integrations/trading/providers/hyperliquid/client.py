import datetime
import logging
import typing

from common import exceptions as common_exceptions
from common import utils as common_utils
from src import enums as src_enums
from src import models as src_models
from src.integrations.trading.gateways.hyperliquid import (
    client as hyperliquid_api_client,
)
from src.integrations.trading.gateways.hyperliquid import (
    exceptions as hyperliquid_api_client_exceptions,
)
from src.integrations.trading.providers import base as base_provider
from src.integrations.trading.providers import exceptions as trading_provider_exceptions
from src.integrations.trading.providers import messages as trading_messages
from src.integrations.trading.providers.hyperliquid import (
    schemas as hyperliquid_schemas,
)

logger = logging.getLogger(__name__)


class HyperLiquidProvider(base_provider.BaseProvider):
    def __init__(self) -> None:
        self.log_prefix = "[HYPERLIQUID-PROVIDER]"
        self._api_client = None

    @property
    def provider(self) -> src_enums.TradingProvider:
        return src_enums.TradingProvider.HYPERLIQUID

    @property
    def api_client_class(
        self,
    ) -> typing.Type[hyperliquid_api_client.HyperLiquidApiClient]:
        return hyperliquid_api_client.HyperLiquidApiClient

    @property
    def order_open_statuses(self) -> typing.List[int]:
        return [src_enums.TradeStatus.OPEN.value]

    def get_api_client(self) -> hyperliquid_api_client.HyperLiquidApiClient:
        if not self._api_client:
            self._api_client = self.api_client_class()

        return self._api_client

    def get_order_fills(
        self,
        wallet_address: str,
        from_datetime: datetime.datetime,
        to_datetime: datetime.datetime,
    ) -> typing.List[trading_messages.OrderFill]:
        try:
            response = self.get_api_client().get_order_fills(
                wallet_address=wallet_address
            )
        except hyperliquid_api_client_exceptions.HyperLiquidAPIException as e:
            msg = "Unable to get order fills (wallet_address={}). Error: {}".format(
                wallet_address, common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.log_prefix, msg))
            raise trading_provider_exceptions.TradingProviderApiClientError(msg)

        try:
            validated_data = common_utils.validate_data_schema(
                data={"order_fills": response}, schema=hyperliquid_schemas.OrderFills()
            )
        except common_exceptions.ValidationSchemaException as e:
            msg = "Order fills response data is not valid. Error: {}".format(
                common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.log_prefix, msg))
            raise trading_provider_exceptions.DataValidationError(msg)

        return [
            trading_messages.OrderFill(
                order_id=order_fill["oid"],
                market="{}-USD".format(order_fill["coin"]),
                side=self._get_order_trade_side(order_side=order_fill["side"]),
                direction=self._get_order_trade_direction(
                    order_direction=order_fill["dir"]
                ),
                price=order_fill["px"],
                size=order_fill["sz"],
                fee=order_fill["fee"],
                closed_pnl=order_fill["closedPnl"],
                hash=order_fill["hash"],
                created_at=order_fill["time"] / 1000,
            )
            for order_fill in validated_data["order_fills"]
        ]

    def get_order(self, wallet_address: str, order_id: str) -> trading_messages.Order:
        try:
            response = self.get_api_client().get_order(
                wallet_address=wallet_address, order_id=int(order_id)
            )
        except hyperliquid_api_client_exceptions.HyperLiquidAPIException as e:
            msg = "Unable to get order (wallet_address={}, order_id={}). Error: {}".format(
                wallet_address,
                order_id,
                common_utils.get_exception_message(exception=e),
            )
            logger.exception("{} {}.".format(self.log_prefix, msg))
            raise trading_provider_exceptions.TradingProviderApiClientError(msg)

        try:
            validated_data = common_utils.validate_data_schema(
                data=response, schema=hyperliquid_schemas.Order()
            )
        except common_exceptions.ValidationSchemaException as e:
            msg = "Order fills response data is not valid. Error: {}".format(
                common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.log_prefix, msg))
            raise trading_provider_exceptions.DataValidationError(msg)

        return trading_messages.Order(
            order_id=validated_data["oid"],
            market="{}-USD".format(validated_data["coin"]),
            type=self._get_order_trade_type(order_type=validated_data["orderType"]),
            side=self._get_order_trade_side(order_side=validated_data["side"]),
            status=self._get_order_trade_status(order_status=validated_data["status"]),
            size=validated_data["sz"],
            original_size=validated_data["origSz"],
            created_at=validated_data["timestamp"] / 1000,
        )

    def get_open_order_ids(self, wallet_address: str) -> typing.List[str]:
        try:
            response = self.get_api_client().get_open_orders(
                wallet_address=wallet_address
            )
        except hyperliquid_api_client_exceptions.HyperLiquidAPIException as e:
            msg = "Unable to fetch open orders (wallet_address={}). Error: {}".format(
                wallet_address, common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.log_prefix, msg))
            raise trading_provider_exceptions.TradingProviderApiClientError(msg)

        try:
            validated_data = common_utils.validate_data_schema(
                data={"open_orders": response}, schema=hyperliquid_schemas.OpenOrders()
            )
        except common_exceptions.ValidationSchemaException as e:
            msg = "Open orders response data is not valid. Error: {}".format(
                common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.log_prefix, msg))
            raise trading_provider_exceptions.DataValidationError(msg)

        return [str(open_order["oid"]) for open_order in validated_data["open_orders"]]

    def get_positions(
        self,
        wallet_address: str,
        from_datetime: datetime.datetime,
        to_datetime: datetime.datetime,
    ) -> typing.List[trading_messages.Position]:
        try:
            response = self.get_api_client().get_positions(
                wallet_address=wallet_address
            )
        except hyperliquid_api_client_exceptions.HyperLiquidAPIException as e:
            msg = "Unable to fetch positions (wallet_address={}). Error: {}".format(
                wallet_address, common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.log_prefix, msg))
            raise trading_provider_exceptions.TradingProviderApiClientError(msg)

        try:
            validated_data = common_utils.validate_data_schema(
                data={"positions": response},
                schema=hyperliquid_schemas.Positions(),
            )
        except common_exceptions.ValidationSchemaException as e:
            msg = "Positions response data is not valid. Error: {}".format(
                common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.log_prefix, msg))
            raise trading_provider_exceptions.DataValidationError(msg)

        return [
            trading_messages.Position(
                market="{}-USD".format(position["coin"]),
                status=src_enums.PositionStatus.OPEN,
                size=position["szi"],
                remaining_size=position["szi"],
                side=src_enums.PositionSide.NEUTRAL,
                unrealized_pnl=position["unrealized_pnl"],
                realized_pnl=0,
                value=position["position_value"],
                created_at=datetime.datetime(2000, 1, 1).timestamp(),
                closed_at=None,
            )
            for position in validated_data["positions"]
        ]

    def get_position_fundings(
        self,
        wallet_address: str,
        from_datetime: datetime.datetime,
        to_datetime: typing.Optional[datetime.datetime] = None,
    ) -> typing.List[trading_messages.PositionFunding]:
        try:
            response = self.get_api_client().get_position_fundings(
                wallet_address=wallet_address,
                from_datetime=from_datetime,
                to_datetime=to_datetime,
            )
        except hyperliquid_api_client_exceptions.HyperLiquidAPIException as e:
            msg = "Unable to fetch position fundings (wallet_address={}, from_datetime={}, to_datetime={}). Error: {}".format(
                wallet_address,
                from_datetime,
                to_datetime,
                common_utils.get_exception_message(exception=e),
            )
            logger.exception("{} {}.".format(self.log_prefix, msg))
            raise trading_provider_exceptions.TradingProviderApiClientError(msg)

        try:
            validated_data = common_utils.validate_data_schema(
                data={"position_fundings": response},
                schema=hyperliquid_schemas.PositionFundings(),
            )
        except common_exceptions.ValidationSchemaException as e:
            msg = "Position fundings response data is not valid. Error: {}".format(
                common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.log_prefix, msg))
            raise trading_provider_exceptions.DataValidationError(msg)

        return [
            trading_messages.PositionFunding(
                market="{}-USD".format(position_funding["coin"]),
                payment=position_funding["payment"],
                funding_rate=position_funding["funding_rate"],
                position_size=position_funding["position_size"],
                hash=position_funding["hash"],
                created_at=position_funding["timestamp"] / 1000,
            )
            for position_funding in validated_data["position_fundings"]
        ]

    def prepare_order_fill_for_import(
        self, order_fill: trading_messages.OrderFill, order: src_models.Order
    ) -> trading_messages.OrderFillImportData:
        return trading_messages.OrderFillImportData(
            order_id=order_fill.order_id,
            market=order_fill.market,
            side=order_fill.side,
            position_side=src_enums.PositionSide[
                order_fill.direction.name.split("_")[-1]
            ],
            direction=order_fill.direction,
            price=order_fill.price,
            size=order_fill.size,
            fee=order_fill.fee,
            closed_pnl=order_fill.closed_pnl,
            hash=order_fill.hash,
            created_at=order_fill.created_at,
        )

    def get_account_portfolio(
        self, wallet_address: str
    ) -> trading_messages.WalletAccount:
        try:
            response = self.get_api_client().get_account(wallet_address=wallet_address)
        except hyperliquid_api_client_exceptions.HyperLiquidAPIException as e:
            msg = (
                "Unable to get account portfolio (wallet_address={}). Error: {}".format(
                    wallet_address,
                    common_utils.get_exception_message(exception=e),
                )
            )
            logger.exception("{} {}.".format(self.log_prefix, msg))
            raise trading_provider_exceptions.TradingProviderApiClientError(msg)

        try:
            validated_data = common_utils.validate_data_schema(
                data=response, schema=hyperliquid_schemas.AccountPortfolio()
            )
        except common_exceptions.ValidationSchemaException as e:
            msg = "Account portfolio response data is not valid. Error: {}".format(
                common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.log_prefix, msg))
            raise trading_provider_exceptions.DataValidationError(msg)

        return trading_messages.WalletAccount(
            equity_value=validated_data["equity_value"]
        )

    @staticmethod
    def _get_order_trade_side(order_side: str) -> src_enums.TradeSide:
        return {"A": src_enums.TradeSide.SELL, "B": src_enums.TradeSide.BUY}[order_side]

    @staticmethod
    def _get_order_trade_direction(order_direction: str) -> src_enums.TradeDirection:
        return {
            "Open Long": src_enums.TradeDirection.OPEN_LONG,
            "Close Long": src_enums.TradeDirection.CLOSE_LONG,
            "Open Short": src_enums.TradeDirection.OPEN_SHORT,
            "Close Short": src_enums.TradeDirection.CLOSE_SHORT,
        }[order_direction]

    @staticmethod
    def _get_order_trade_type(order_type: str) -> src_enums.TradeType:
        return {
            "Stop Market": src_enums.TradeType.STOP_MARKET,
            "Market": src_enums.TradeType.MARKET,
            "Limit": src_enums.TradeType.LIMIT,
        }[order_type]

    @staticmethod
    def _get_order_trade_status(order_status: str) -> src_enums.TradeStatus:
        return {
            "filled": src_enums.TradeStatus.FILLED,
            "open": src_enums.TradeStatus.OPEN,
            "canceled": src_enums.TradeStatus.CANCELLED,
        }[order_status]
