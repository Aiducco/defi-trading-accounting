import datetime
import logging
import typing

from django.db import models as django_db_models

from common import utils as common_utils
from src import enums as src_enums
from src import models as src_models
from src.integrations.trading.providers import base as base_provider
from src.integrations.trading.providers import constants as trading_constants
from src.integrations.trading.providers import exceptions as trading_exceptions

logger = logging.getLogger(__name__)


class TradingDataImporter(object):
    def __init__(self, trading_data_provider: base_provider.BaseProvider) -> None:
        self.trading_data_provider_client = trading_data_provider

        self.log_prefix = "[TRADING-DATA-IMPORTER-SERVICE-{}]".format(
            self.trading_data_provider_client.provider.name
        )

    def import_open_trade_orders(self, wallet_address: str) -> None:
        accounting_wallet = src_models.AccountingWallet.objects.filter(
            address=wallet_address,
            provider=self.trading_data_provider_client.provider.value,
        ).first()
        if not accounting_wallet:
            logger.info(
                "{} Accounting wallet (address={}) is not found. Exiting.".format(
                    self.log_prefix, wallet_address
                )
            )
            return

        try:
            open_trade_order_ids = self.trading_data_provider_client.get_open_order_ids(
                wallet_address=wallet_address
            )
        except trading_exceptions.TradingProviderClientError:
            logger.exception(
                "{} Unable to fetch open trade orders (wallet_address={}). Exiting.".format(
                    self.log_prefix, wallet_address
                )
            )
            return

        if not open_trade_order_ids:
            logger.info(
                "{} No open trade order ids to import (accounting_wallet_id={}). Exiting.".format(
                    self.log_prefix, accounting_wallet.id
                )
            )
            return

        logger.info(
            "{} Fetched {} open trade order ids to import (accounting_wallet_id={}, order_ids={}).".format(
                self.log_prefix,
                len(open_trade_order_ids),
                accounting_wallet.id,
                open_trade_order_ids,
            )
        )

        for open_trade_order_id in open_trade_order_ids:
            try:
                self._import_trade_order(
                    accounting_wallet=accounting_wallet, order_id=open_trade_order_id
                )
            except Exception as e:
                logger.exception(
                    "{} Unable to import trade order (order_id={}). Error: {}. Continue.".format(
                        self.log_prefix,
                        open_trade_order_id,
                        common_utils.get_exception_message(exception=e),
                    )
                )
                continue

        stale_open_order_ids = (
            src_models.Order.objects.filter(
                status__in=self.trading_data_provider_client.order_open_statuses,
                wallet=accounting_wallet,
            )
            .exclude(django_db_models.Q(order_id__in=open_trade_order_ids))
            .values_list("order_id", flat=True)
        )
        logger.info(
            "{} Found {} stale open orders to recheck and reimport.".format(
                self.log_prefix, len(stale_open_order_ids)
            )
        )
        for open_stale_trade_order_id in stale_open_order_ids:
            try:
                self._import_trade_order(
                    accounting_wallet=accounting_wallet,
                    order_id=open_stale_trade_order_id,
                )
            except Exception as e:
                logger.exception(
                    "{} Unable to reimport stale trade order (order_id={}). Error: {}. Continue.".format(
                        self.log_prefix,
                        open_stale_trade_order_id,
                        common_utils.get_exception_message(exception=e),
                    )
                )

        logger.info(
            "{} Finished importing open orders (accounting_wallet_id={}).".format(
                self.log_prefix, accounting_wallet.id
            )
        )

    def import_trade_orders(
        self,
        wallet_address: str,
        from_datetime: typing.Optional[datetime.datetime] = None,
        to_datetime: typing.Optional[datetime.datetime] = None,
    ) -> None:
        accounting_wallet = src_models.AccountingWallet.objects.filter(
            address=wallet_address,
            provider=self.trading_data_provider_client.provider.value,
        ).first()
        if not accounting_wallet:
            logger.info(
                "{} Accounting wallet (address={}) is not found. Exiting.".format(
                    self.log_prefix, wallet_address
                )
            )
            return

        if not (from_datetime and to_datetime):
            logger.info(
                "{} Either both from_datetime and to_datetime have to be specified or neither. Exiting.".format(
                    self.log_prefix
                )
            )
            return

        if not from_datetime:
            last_order_fill = (
                src_models.OrderFill.objects.filter(order__wallet=accounting_wallet)
                .order_by("order_fill_timestamp")
                .last()
            )
            if not last_order_fill:
                logger.info(
                    "{} No order trades found in the db for accounting wallet (id={}, address={}). Please set date range for importing. Exiting.".format(
                        self.log_prefix, accounting_wallet.id, accounting_wallet.address
                    )
                )
                return

            from_datetime = datetime.datetime.fromtimestamp(last_order_fill.timestamp)
            to_datetime = from_datetime + datetime.timedelta(
                days=trading_constants.TRADE_ORDERS_IMPORTING_TIME_DELTA
            )

        logger.info(
            "{} Started importing order trades (accounting_wallet_id={}, wallet_address={}, from_datetime={}, to_datetime={}).".format(
                self.log_prefix,
                accounting_wallet.id,
                accounting_wallet.address,
                from_datetime,
                to_datetime,
            )
        )

        try:
            self._import_trade_order_history(
                accounting_wallet=accounting_wallet,
                from_datetime=from_datetime,
                to_datetime=to_datetime,
            )
        except trading_exceptions.TradingProviderClientError as e:
            logger.exception(
                "{} Unable to import trade order history. Error: {}. Exiting.".format(
                    self.log_prefix, common_utils.get_exception_message(exception=e)
                )
            )
            return

        logger.info(
            "{} Finished importing order trades (accounting_wallet_id={}, wallet_address={}, from_datetime={}, to_datetime={}).".format(
                self.log_prefix,
                accounting_wallet.id,
                accounting_wallet.address,
                from_datetime,
                to_datetime,
            )
        )

    def _import_trade_order_history(
        self,
        accounting_wallet: src_models.AccountingWallet,
        from_datetime: datetime.datetime,
        to_datetime: datetime.datetime,
    ) -> None:
        order_fills = self.trading_data_provider_client.get_order_fills(
            wallet_address=accounting_wallet.address,
            from_datetime=from_datetime,
            to_datetime=to_datetime,
        )

        if not order_fills:
            logger.info(
                "{} Found no order fills to import (accounting_wallet_id={}, wallet_address={}). Exiting.".format(
                    self.log_prefix, accounting_wallet.id, accounting_wallet.address
                )
            )
            return

        logger.info(
            "{} Found {} order fills to import (accounting_wallet_id={}, wallet_address={}).".format(
                self.log_prefix,
                len(order_fills),
                accounting_wallet.id,
                accounting_wallet.address,
            )
        )

        for order_fill in order_fills:
            try:
                trade_order = self._import_trade_order(
                    accounting_wallet=accounting_wallet, order_id=order_fill.order_id
                )
                order_fill_to_import = (
                    self.trading_data_provider_client.prepare_order_fill_for_import(
                        order_fill=order_fill, order=trade_order
                    )
                )
                order_fill, created = src_models.OrderFill.objects.get_or_create(
                    price=order_fill_to_import.price,
                    size=order_fill_to_import.size,
                    side=order_fill_to_import.side.value,
                    side_name=order_fill_to_import.side.name,
                    position_side=order_fill_to_import.position_side.value,
                    position_side_name=order_fill_to_import.position_side.name,
                    direction=order_fill_to_import.direction.value
                    if order_fill_to_import.direction
                    else None,
                    direction_name=order_fill_to_import.direction.name
                    if order_fill_to_import.direction
                    else None,
                    hash=order_fill_to_import.hash,
                    order_fill_timestamp=order_fill_to_import.created_at,
                    order=trade_order,
                    defaults={
                        "order_fill_created_at": common_utils.convert_from_timestamp(
                            timestamp=order_fill_to_import.created_at
                        ),
                        "closed_pnl": order_fill_to_import.closed_pnl,
                        "fee": order_fill_to_import.fee,
                    },
                )
                if not created:
                    logger.info(
                        "Order fill already exists (id={}).".format(order_fill.id)
                    )
            except Exception as e:
                logger.exception(
                    "{} Unable to import order fill (order_id={}, raw_data={}). Error: {}. Continue.".format(
                        self.log_prefix,
                        order_fill.order_id,
                        order_fill,
                        common_utils.get_exception_message(exception=e),
                    )
                )
                continue

        logger.info(
            "{} Finished importing {} order fills (accounting_wallet_id={}, wallet_address={}).".format(
                self.log_prefix,
                len(order_fills),
                accounting_wallet.id,
                accounting_wallet.address,
            )
        )

    def _import_trade_order(
        self, accounting_wallet: src_models.AccountingWallet, order_id: str
    ) -> src_models.Order:
        order = self.trading_data_provider_client.get_order(
            wallet_address=accounting_wallet.address, order_id=order_id
        )

        db_order = src_models.Order.objects.filter(order_id=order_id).first()
        if db_order:
            db_order.status = order.status.value
            db_order.status_name = order.status.name
            db_order.remaining_size = order.size
            db_order.save(
                update_fields=["status", "status_name", "remaining_size", "updated_at"]
            )

            return db_order

        return src_models.Order.objects.create(
            order_id=order.order_id,
            market=order.market,
            type=order.type.value,
            type_name=order.type.name,
            side=order.side.value,
            side_name=order.side.name,
            status=order.status.value,
            status_name=order.status.name,
            original_size=order.original_size,
            remaining_size=order.size,
            order_timestamp=order.created_at,
            order_created_at=common_utils.convert_from_timestamp(
                timestamp=order.created_at
            ),
            wallet=accounting_wallet,
        )

    def import_trade_positions(
        self,
        wallet_address: str,
        from_datetime: datetime.datetime,
        to_datetime: datetime.datetime,
    ) -> None:
        accounting_wallet = src_models.AccountingWallet.objects.filter(
            address=wallet_address,
            provider=self.trading_data_provider_client.provider.value,
        ).first()
        if not accounting_wallet:
            logger.info(
                "{} Accounting wallet (address={}) is not found. Exiting.".format(
                    self.log_prefix, wallet_address
                )
            )
            return

        try:
            trade_positions = self.trading_data_provider_client.get_positions(
                wallet_address=wallet_address,
                from_datetime=from_datetime,
                to_datetime=to_datetime,
            )
        except trading_exceptions.TradingProviderClientError:
            logger.exception(
                "{} Unable to fetch trade positions (accounting_wallet_id={}, from_datetime={}, to_datetime={}). Exiting.".format(
                    self.log_prefix, accounting_wallet.id, from_datetime, to_datetime
                )
            )
            return

        if not trade_positions:
            """
            If there are no trade positions fetched from the API we remove zombie positions.
            This is okay for now since we do not fetch positions by actual datetime range. This is needed by Hyperliquid.
             Otherwise the correct way to do it is to have a scheduled task which fetches and checks position status.
            """
            src_models.Position.objects.filter(
                status=src_enums.PositionStatus.OPEN.value, wallet=accounting_wallet
            ).delete()

            logger.info(
                "{} No trade positions to import (accounting_wallet_id={}, from_datetime={}, to_datetime={})."
                " Removed zombie positions.".format(
                    self.log_prefix, accounting_wallet.id, from_datetime, to_datetime
                )
            )
            return

        logger.info(
            "{} Fetched {} trade positions to import (accounting_wallet_id={}, from_datetime={}, to_datetime={}).".format(
                self.log_prefix,
                len(trade_positions),
                accounting_wallet.id,
                from_datetime,
                to_datetime,
            )
        )

        for trade_position in trade_positions:
            position_closed_at = (
                common_utils.convert_from_timestamp(timestamp=trade_position.closed_at)
                if trade_position.closed_at
                else None
            )
            position, created = src_models.Position.objects.get_or_create(
                market=trade_position.market,
                side=trade_position.side.value,
                wallet=accounting_wallet,
                position_created_at=common_utils.convert_from_timestamp(
                    timestamp=trade_position.created_at
                ),
                defaults={
                    "status": trade_position.status.value,
                    "status_name": trade_position.status.name,
                    "side_name": trade_position.side.name,
                    "size": trade_position.size,
                    "remaining_size": trade_position.remaining_size,
                    "unrealized_pnl": trade_position.unrealized_pnl,
                    "realized_pnl": trade_position.realized_pnl,
                    "value": trade_position.value,
                    "position_closed_at": position_closed_at,
                },
            )
            if not created:
                position.status = trade_position.status.value
                position.status_name = trade_position.status.name
                position.size = trade_position.size
                position.remaining_size = trade_position.remaining_size
                position.unrealized_pnl = trade_position.unrealized_pnl
                position.realized_pnl = trade_position.realized_pnl
                position.value = trade_position.value
                position.position_closed_at = position_closed_at

                position.save(
                    update_fields=[
                        "status",
                        "status_name",
                        "size",
                        "remaining_size",
                        "unrealized_pnl",
                        "realized_pnl",
                        "value",
                        "position_closed_at",
                        "updated_at",
                    ]
                )

        logger.info(
            "{} Finished importing trade positions (accounting_wallet_id={}, from_datetime={}, to_datetime={}).".format(
                self.log_prefix,
                len(trade_positions),
                accounting_wallet.id,
                from_datetime,
                to_datetime,
            )
        )

    def import_position_fundings(
        self,
        wallet_address: str,
        from_datetime: typing.Optional[datetime.datetime] = None,
        to_datetime: typing.Optional[datetime.datetime] = None,
    ):
        accounting_wallet = src_models.AccountingWallet.objects.filter(
            address=wallet_address,
            provider=self.trading_data_provider_client.provider.value,
        ).first()
        if not accounting_wallet:
            logger.info(
                "{} Accounting wallet (address={}) is not found. Exiting.".format(
                    self.log_prefix, wallet_address
                )
            )
            return

        if not from_datetime and to_datetime:
            logger.error(
                "{} Have to set from_datetime when using to_datetine. Exiting."
            )
            return

        if not from_datetime:
            position_funding = (
                src_models.FundingPayment.objects.filter(wallet=accounting_wallet)
                .order_by("funding_created_at")
                .last()
            )
            if not position_funding:
                logger.info(
                    "{} No position funding found (accounting_wallet_id={}). Exiting.".format(
                        self.log_prefix, accounting_wallet.id
                    )
                )
                return

            from_datetime = position_funding.funding_created_at

        try:
            position_fundings = self.trading_data_provider_client.get_position_fundings(
                wallet_address=wallet_address,
                from_datetime=from_datetime,
                to_datetime=to_datetime,
            )
        except trading_exceptions.TradingProviderClientError:
            logger.exception(
                "{} Unable to fetch position fundings to import (accounting_wallet_id={}, from_datetime={}, to_datetime={}). Exiting.".format(
                    self.log_prefix, accounting_wallet.id, from_datetime, to_datetime
                )
            )
            return

        if not position_fundings:
            logger.info(
                "{} No position fundings to import (accounting_wallet_id={}, from_datetime={}, to_datetime={}). Exiting.".format(
                    self.log_prefix, accounting_wallet.id, from_datetime, to_datetime
                )
            )
            return

        logger.info(
            "{} Fetched {} position fundings to import (accounting_wallet_id={}, from_datetime={}, to_datetime={}).".format(
                self.log_prefix,
                len(position_fundings),
                accounting_wallet.id,
                from_datetime,
                to_datetime,
            )
        )
        for position_funding in position_fundings:
            src_models.FundingPayment.objects.get_or_create(
                market=position_funding.market,
                wallet=accounting_wallet,
                payment=position_funding.payment,
                funding_rate=position_funding.funding_rate,
                position_size=position_funding.position_size,
                hash=position_funding.hash,
                defaults={
                    "funding_created_at": common_utils.convert_from_timestamp(
                        timestamp=position_funding.created_at
                    ),
                    "funding_timestamp": position_funding.created_at,
                },
            )

        logger.info(
            "{} Imported position fundings (accounting_wallet_id={}, from_datetime={}, to_datetime={}).".format(
                self.log_prefix,
                accounting_wallet.id,
                from_datetime,
                to_datetime,
            )
        )

    def import_wallet_portfolio(self, wallet_address: str) -> None:
        accounting_wallet = src_models.AccountingWallet.objects.filter(
            address=wallet_address,
            provider=self.trading_data_provider_client.provider.value,
        ).first()
        if not accounting_wallet:
            logger.info(
                "{} Accounting wallet (address={}) is not found. Exiting.".format(
                    self.log_prefix, wallet_address
                )
            )
            return

        try:
            wallet_portfolio = self.trading_data_provider_client.get_account_portfolio(
                wallet_address=wallet_address
            )
        except trading_exceptions.TradingProviderClientError:
            logger.exception(
                "{} Unable to fetch wallet portfolio (accounting_wallet_id={}). Exiting.".format(
                    self.log_prefix, accounting_wallet.id
                )
            )
            return

        portfolio_value = src_models.Position.objects.filter(
            wallet_id=accounting_wallet.id,
            status=src_enums.PositionStatus.OPEN.value,
        ).aggregate(total_value=django_db_models.Sum("value"))["total_value"]

        portfolio_value = portfolio_value or 0

        (
            account_wallet_portfolio,
            created,
        ) = src_models.WalletPortfolio.objects.get_or_create(
            wallet_id=accounting_wallet.id,
            portfolio_date=datetime.datetime.now().date(),
            defaults={
                "equity_value": wallet_portfolio.equity_value,
                "portfolio_value": portfolio_value,
            },
        )

        if not created:
            account_wallet_portfolio.equity_value = wallet_portfolio.equity_value
            account_wallet_portfolio.portfolio_value = portfolio_value
            account_wallet_portfolio.save(
                update_fields=["equity_value", "portfolio_value", "updated_at"]
            )

        logger.info(
            "{} Updated account wallet portfolio (id={}).".format(
                self.log_prefix, account_wallet_portfolio.id
            )
        )
