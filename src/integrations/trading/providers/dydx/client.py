import datetime
import decimal
import logging
import typing

from common import exceptions as common_exceptions
from common import utils as common_utils
from src import enums as src_enums
from src import models as src_models
from src.integrations.trading.gateways.dydx import client as dydx_api_client
from src.integrations.trading.gateways.dydx import (
    exceptions as dydx_api_client_exceptions,
)
from src.integrations.trading.providers import base as base_provider
from src.integrations.trading.providers import exceptions as trading_provider_exceptions
from src.integrations.trading.providers import messages as trading_messages
from src.integrations.trading.providers.dydx import schemas as dydx_schemas

logger = logging.getLogger(__name__)


class DyDxProvider(base_provider.BaseProvider):
    def __init__(self) -> None:
        self.log_prefix = "[HYPERLIQUID-PROVIDER]"

    @property
    def provider(self) -> src_enums.TradingProvider:
        return src_enums.TradingProvider.DYDX

    @property
    def api_client_class(self) -> typing.Type[dydx_api_client.DYDXApiClient]:
        return dydx_api_client.DYDXApiClient

    @property
    def order_open_statuses(self) -> typing.List[int]:
        return [
            src_enums.TradeStatus.OPEN.value,
            src_enums.TradeStatus.PENDING.value,
            src_enums.TradeStatus.UNTRIGGERED.value,
        ]

    def get_api_client(self, wallet_address: str) -> dydx_api_client.DYDXApiClient:
        return self.api_client_class(wallet_address=wallet_address)

    def get_order_fills(
        self,
        wallet_address: str,
        from_datetime: datetime.datetime,
        to_datetime: datetime.datetime,
    ) -> typing.List[trading_messages.OrderFill]:
        try:
            response = self.get_api_client(
                wallet_address=wallet_address
            ).get_order_fills()
        except dydx_api_client_exceptions.DYDXAPIException as e:
            msg = "Unable to get order fills (wallet_address={}). Error: {}".format(
                wallet_address, common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.log_prefix, msg))
            raise trading_provider_exceptions.TradingProviderApiClientError(msg)

        try:
            validated_data = common_utils.validate_data_schema(
                data={"order_fills": response}, schema=dydx_schemas.OrderFills()
            )
        except common_exceptions.ValidationSchemaException as e:
            msg = "Order fills response data is not valid. Error: {}".format(
                common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.log_prefix, msg))
            raise trading_provider_exceptions.DataValidationError(msg)

        return [
            trading_messages.OrderFill(
                order_id=order_fill["order_id"],
                market=order_fill["market"],
                side=self._get_order_trade_side(order_side=order_fill["side"]),
                direction=None,
                price=order_fill["price"],
                size=order_fill["size"],
                fee=order_fill["fee"],
                closed_pnl=None,
                hash=order_fill["id"],
                created_at=order_fill["created_at"].timestamp(),
            )
            for order_fill in validated_data["order_fills"]
        ]

    def get_order(self, wallet_address: str, order_id: str) -> trading_messages.Order:
        try:
            response = self.get_api_client(wallet_address=wallet_address).get_order(
                order_id=order_id
            )
        except dydx_api_client_exceptions.DYDXAPIException as e:
            msg = "Unable to get order (wallet_address={}, order_id={}). Error: {}".format(
                wallet_address,
                order_id,
                common_utils.get_exception_message(exception=e),
            )
            logger.exception("{} {}.".format(self.log_prefix, msg))
            raise trading_provider_exceptions.TradingProviderApiClientError(msg)

        try:
            validated_data = common_utils.validate_data_schema(
                data=response, schema=dydx_schemas.Order()
            )
        except common_exceptions.ValidationSchemaException as e:
            msg = "Order response data is not valid. Error: {}".format(
                common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.log_prefix, msg))
            raise trading_provider_exceptions.DataValidationError(msg)

        return trading_messages.Order(
            order_id=validated_data["id"],
            market=validated_data["market"],
            type=self._get_order_trade_type(order_type=validated_data["type"]),
            side=self._get_order_trade_side(order_side=validated_data["side"]),
            status=self._get_order_trade_status(order_status=validated_data["status"]),
            size=validated_data["remaining_size"],
            original_size=validated_data["size"],
            created_at=validated_data["created_at"].timestamp(),
        )

    def get_open_order_ids(self, wallet_address: str) -> typing.List[str]:
        try:
            response = self.get_api_client(wallet_address=wallet_address).get_orders()
        except dydx_api_client_exceptions.DYDXAPIException as e:
            msg = "Unable to fetch open orders (wallet_address={}). Error: {}".format(
                wallet_address, common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.log_prefix, msg))
            raise trading_provider_exceptions.TradingProviderApiClientError(msg)

        try:
            validated_data = common_utils.validate_data_schema(
                data={"orders": response}, schema=dydx_schemas.Orders()
            )
        except common_exceptions.ValidationSchemaException as e:
            msg = "Open orders response data is not valid. Error: {}".format(
                common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.log_prefix, msg))
            raise trading_provider_exceptions.DataValidationError(msg)

        return [str(open_order["id"]) for open_order in validated_data["orders"]]

    def get_positions(
        self,
        wallet_address: str,
        from_datetime: datetime.datetime,
        to_datetime: datetime.datetime,
    ) -> typing.List[trading_messages.Position]:
        try:
            response = self.get_api_client(
                wallet_address=wallet_address
            ).get_positions()
        except dydx_api_client_exceptions.DYDXAPIException as e:
            msg = "Unable to fetch positions (wallet_address={}). Error: {}".format(
                wallet_address, common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.log_prefix, msg))
            raise trading_provider_exceptions.TradingProviderApiClientError(msg)

        try:
            validated_data = common_utils.validate_data_schema(
                data={"positions": response},
                schema=dydx_schemas.Positions(),
            )
        except common_exceptions.ValidationSchemaException as e:
            msg = "Positions response data is not valid. Error: {}".format(
                common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.log_prefix, msg))
            raise trading_provider_exceptions.DataValidationError(msg)

        return [
            trading_messages.Position(
                market=position["market"],
                status=self._get_position_status(position_status=position["status"]),
                side=self._get_position_side(position_side=position["side"]),
                size=abs(float(position["max_size"])),
                remaining_size=abs(float(position["size"])),
                unrealized_pnl=position["unrealized_pnl"],
                realized_pnl=position["realized_pnl"],
                value=float(position["size"])
                * self.get_market_price(
                    wallet_address=wallet_address, market=position["market"]
                ),  # NOTE: This is not the optimal way. This could be cached etc.
                created_at=position["created_at"].timestamp(),
                closed_at=position["closed_at"].timestamp()
                if position["closed_at"]
                else None,
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
            response = self.get_api_client(
                wallet_address=wallet_address
            ).get_funding_payments()
        except dydx_api_client_exceptions.DYDXAPIException as e:
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
                schema=dydx_schemas.PositionFundings(),
            )
        except common_exceptions.ValidationSchemaException as e:
            msg = "Position fundings response data is not valid. Error: {}".format(
                common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.log_prefix, msg))
            raise trading_provider_exceptions.DataValidationError(msg)

        return [
            trading_messages.PositionFunding(
                market=position_funding["market"],
                payment=position_funding["payment"],
                funding_rate=position_funding["rate"],
                position_size=position_funding["position_size"],
                hash=None,
                created_at=position_funding["effective_at"].timestamp(),
            )
            for position_funding in validated_data["position_fundings"]
        ]

    def prepare_order_fill_for_import(
        self, order_fill: trading_messages.OrderFill, order: src_models.Order
    ) -> trading_messages.OrderFillImportData:
        position = src_models.Position.objects.filter(
            wallet=order.wallet,
            market=order.market,
            status=src_enums.PositionStatus.CLOSED.value,
            position_created_at__lte=order.order_created_at.replace(
                microsecond=0, second=0
            ),
            position_closed_at__gte=order.order_created_at.replace(
                microsecond=0, second=0
            ),
        ).first()

        if not position and order.status in [
            src_enums.TradeStatus.OPEN.value,
            src_enums.TradeStatus.FILLED.value,
            src_enums.TradeStatus.CANCELLED.value,
        ]:
            position = src_models.Position.objects.filter(
                wallet=order.wallet,
                market=order.market,
                status=src_enums.PositionStatus.OPEN.value,
                position_created_at__lte=order.order_created_at.replace(
                    microsecond=0, second=0
                ),
            ).first()

        if not position:
            msg = "Unable to find position (order_fill{}, order_id={}, order_created_at={}). Skipping.".format(
                order_fill, order.id, order.order_created_at
            )
            logger.error("{} {}.".format(self.log_prefix, msg))
            raise trading_provider_exceptions.PositionNotFoundError(msg)

        filled_size = position.size - position.remaining_size
        closed_pnl = 0
        if order.side == src_enums.TradeSide.SELL.value:
            closed_pnl = (
                (float(order_fill.size) / position.size) * position.realized_pnl
                if filled_size
                else 0
            )

        return trading_messages.OrderFillImportData(
            order_id=order_fill.order_id,
            market=order_fill.market,
            side=order_fill.side,
            position_side=src_enums.PositionSide(position.side) if position else None,
            direction=src_enums.TradeDirection.from_order_side_and_position_side(
                order_side=src_enums.TradeSide(order.side),
                position_side=src_enums.PositionSide(position.side),
            )
            if position
            else None,
            price=order_fill.price,
            size=order_fill.size,
            fee=order_fill.fee,
            closed_pnl=closed_pnl,
            hash=order_fill.hash,
            created_at=order_fill.created_at,
        )

    def get_account_portfolio(
        self, wallet_address: str
    ) -> trading_messages.WalletAccount:
        try:
            response = self.get_api_client(wallet_address=wallet_address).get_account()
        except dydx_api_client_exceptions.DYDXAPIException as e:
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
                data=response, schema=dydx_schemas.AccountPortfolio()
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

    def get_market_price(self, wallet_address: str, market: str) -> float:
        try:
            response = self.get_api_client(wallet_address=wallet_address).get_markets(
                market=market
            )
        except dydx_api_client_exceptions.DYDXAPIException as e:
            msg = "Unable to get market data (wallet_address={}, market={}). Error: {}".format(
                wallet_address,
                market,
                common_utils.get_exception_message(exception=e),
            )
            logger.exception("{} {}.".format(self.log_prefix, msg))
            raise trading_provider_exceptions.TradingProviderApiClientError(msg)

        try:
            validated_data = common_utils.validate_data_schema(
                data=response[market], schema=dydx_schemas.Market()
            )
        except common_exceptions.ValidationSchemaException as e:
            msg = "Market response data is not valid. Error: {}".format(
                common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.log_prefix, msg))
            raise trading_provider_exceptions.DataValidationError(msg)

        return validated_data["oracle_price"]

    @staticmethod
    def _get_order_trade_type(order_type: str) -> src_enums.TradeType:
        return {
            "MARKET": src_enums.TradeType.MARKET,
            "LIMIT": src_enums.TradeType.LIMIT,
            "STOP": src_enums.TradeType.STOP,
            "TRAILING_STOP": src_enums.TradeType.TRAILING_STOP,
            "TAKE_PROFIT": src_enums.TradeType.TAKE_PROFIT,
            "STOP_MARKET": src_enums.TradeType.STOP_MARKET,
        }[order_type]

    @staticmethod
    def _get_order_trade_status(order_status: str) -> src_enums.TradeStatus:
        return {
            "FILLED": src_enums.TradeStatus.FILLED,
            "CANCELED": src_enums.TradeStatus.CANCELLED,
            "UNTRIGGERED": src_enums.TradeStatus.UNTRIGGERED,
            "PENDING": src_enums.TradeStatus.PENDING,
            "OPEN": src_enums.TradeStatus.OPEN,
        }[order_status]

    @staticmethod
    def _get_order_trade_side(order_side: str) -> src_enums.TradeSide:
        return {"SELL": src_enums.TradeSide.SELL, "BUY": src_enums.TradeSide.BUY}[
            order_side
        ]

    @staticmethod
    def _get_position_status(position_status: str) -> src_enums.PositionStatus:
        return {
            "OPEN": src_enums.PositionStatus.OPEN,
            "CLOSED": src_enums.PositionStatus.CLOSED,
            "LIQUIDATED": src_enums.PositionStatus.LIQUIDATED,
        }[position_status]

    @staticmethod
    def _get_position_side(position_side: str) -> src_enums.PositionSide:
        return {
            "LONG": src_enums.PositionSide.LONG,
            "SHORT": src_enums.PositionSide.SHORT,
        }[position_side]
