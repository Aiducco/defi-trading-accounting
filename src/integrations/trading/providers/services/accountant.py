"""
PnL Group by day/month etc
"""
import datetime
import logging
import typing

from django.db import models as django_db_models

from src import enums as src_enums
from src import models as src_models
from src.integrations.trading.providers import base as base_provider
from src.integrations.trading.providers import exceptions as provider_exceptions
from src.integrations.trading.providers import messages as provider_messages

logger = logging.getLogger(__name__)


class TradingAccountant(object):
    def __init__(self, trading_data_provider: base_provider.BaseProvider) -> None:
        self.trading_data_provider_client = trading_data_provider

        self.log_prefix = "[TRADING-ACCOUNTANT-SERVICE-{}]".format(
            self.trading_data_provider_client.provider.name
        )

    def get_order_history(
        self,
        wallet_address: str,
        from_datetime: typing.Optional[datetime.datetime] = None,
        to_datetime: typing.Optional[datetime.datetime] = None,
    ) -> typing.List[provider_messages.OrderHistory]:
        order_histories = []
        accounting_wallet = src_models.AccountingWallet.objects.filter(
            address=wallet_address,
            provider=self.trading_data_provider_client.provider.value,
        ).first()
        if not accounting_wallet:
            msg = "Accounting wallet (address={}) is not found".format(wallet_address)
            logger.error("{} {}.".format(self.log_prefix, msg))
            raise provider_exceptions.AccountingWalletNotFoundError(msg)

        filtering = {}
        if from_datetime:
            filtering["order__order_created_at__gte"] = from_datetime

        if to_datetime:
            filtering["order__order_created_at__lte"] = to_datetime

        logger.info(
            "{} Fetching order trade history (wallet_address={}, from_datetime={}, to_datetime={}).".format(
                self.log_prefix, wallet_address, from_datetime, to_datetime
            )
        )

        # Orders with order fills - can be OPEN order still
        for order_trade in (
            src_models.OrderFill.objects.filter(
                order__wallet=accounting_wallet, **filtering
            )
            # .exclude(order__status=src_enums.TradeStatus.OPEN.value)
            .values("order_id")
            .annotate(
                total_size=django_db_models.Sum("size"),
                total_fee=django_db_models.Sum("fee"),
                closed_pnl=django_db_models.Sum("closed_pnl"),
                avg_price=django_db_models.Avg("price"),
            )
            .values(
                "avg_price",
                "total_size",
                "total_fee",
                "closed_pnl",
                "order__status_name",
                "order__side_name",
                "order__type_name",
                "order__order_id",
                "order__order_created_at",
                "order__market",
            )
            .order_by("-order__order_created_at")
        ):
            order_histories.append(
                provider_messages.OrderHistory(
                    wallet_address=wallet_address,
                    provider_name=self.trading_data_provider_client.provider.name,
                    market=order_trade["order__market"],
                    order_id=order_trade["order__order_id"],
                    trade_side=order_trade["order__side_name"],
                    trade_type=order_trade["order__type_name"],
                    trade_status=order_trade["order__status_name"],
                    price=order_trade["avg_price"],
                    size=order_trade["total_size"],
                    fee=order_trade["total_fee"],
                    pnl=order_trade["closed_pnl"],
                    created_at=order_trade["order__order_created_at"].isoformat(),
                )
            )

        # Open orders
        for open_order in src_models.Order.objects.filter(
            wallet=accounting_wallet,
            status=src_enums.TradeStatus.OPEN.value,
            orderfills=None,
        ).order_by("-order_created_at"):
            position = src_models.Position.objects.filter(
                status=src_enums.PositionStatus.OPEN.value,
                market=open_order.market,
                wallet=accounting_wallet,
            ).first()
            if not position:
                logger.error(
                    '{} Unable to find position (open_order_id={}) for market "{}". Continue.'.format(
                        self.log_prefix, open_order.id, open_order.market
                    )
                )
                continue

            order_histories.append(
                provider_messages.OrderHistory(
                    wallet_address=wallet_address,
                    provider_name=self.trading_data_provider_client.provider.name,
                    market=open_order.market,
                    order_id=open_order.order_id,
                    trade_side=open_order.side_name,
                    trade_type=open_order.type_name,
                    trade_status=open_order.status_name,
                    price=0,
                    size=open_order.remaining_size,
                    fee=0,
                    pnl=(open_order.remaining_size / position.remaining_size)
                    * position.unrealized_pnl
                    if open_order.side == src_enums.TradeSide.SELL.value
                    else 0,
                    created_at=open_order.order_created_at.isoformat(),
                )
            )

        # Orders that do not have trade fills
        orders_without_trades = src_models.Order.objects.filter(
            wallet=accounting_wallet, orderfills=None
        ).exclude(django_db_models.Q(status=src_enums.TradeStatus.OPEN.value))
        for order_without_trades in orders_without_trades:
            order_histories.append(
                provider_messages.OrderHistory(
                    wallet_address=wallet_address,
                    provider_name=self.trading_data_provider_client.provider.name,
                    market=order_without_trades.market,
                    order_id=order_without_trades.order_id,
                    trade_side=order_without_trades.side_name,
                    trade_type=order_without_trades.type_name,
                    trade_status=order_without_trades.status_name,
                    price=0,
                    size=order_without_trades.remaining_size,
                    fee=0,
                    pnl=0,
                    created_at=order_without_trades.order_created_at.isoformat(),
                )
            )

        logger.info(
            "{} Fetched order trade history (wallet_address={}, from_datetime={}, to_datetime={}).".format(
                self.log_prefix, wallet_address, from_datetime, to_datetime
            )
        )

        return order_histories

    def get_position_fundings_history(
        self,
        wallet_address: str,
        from_datetime: typing.Optional[datetime.datetime] = None,
        to_datetime: typing.Optional[datetime.datetime] = None,
    ) -> typing.List[provider_messages.PositionFundingHistory]:
        position_funding_histories = []
        accounting_wallet = src_models.AccountingWallet.objects.filter(
            address=wallet_address,
            provider=self.trading_data_provider_client.provider.value,
        ).first()
        if not accounting_wallet:
            msg = "Accounting wallet (address={}) is not found".format(wallet_address)
            logger.error("{} {}.".format(self.log_prefix, msg))
            raise provider_exceptions.AccountingWalletNotFoundError(msg)

        filtering = {}
        if from_datetime:
            filtering["funding_created_at__gte"] = from_datetime

        if to_datetime:
            filtering["funding_created_at__lte"] = to_datetime

        for position_funding in src_models.FundingPayment.objects.filter(
            wallet=accounting_wallet, **filtering
        ):
            position_funding_histories.append(
                provider_messages.PositionFundingHistory(
                    wallet_address=wallet_address,
                    provider_name=self.trading_data_provider_client.provider.name,
                    market=position_funding.market,
                    amount_paid=str(position_funding.payment),
                    funding_rate=str(position_funding.funding_rate),
                    position_size=str(position_funding.position_size),
                    hash=position_funding.hash,
                    created_at=position_funding.created_at.isoformat(),
                )
            )

        logger.info(
            "{} Fetched position funding history (wallet_address={}, from_datetime={}, to_datetime={}).".format(
                self.log_prefix, wallet_address, from_datetime, to_datetime
            )
        )

        return position_funding_histories
