import datetime
import typing

from src import enums as src_enums
from src import models as src_models
from src.integrations.trading.providers import factory
from src.integrations.trading.providers.services import accountant


def get_trade_history_report(
    wallet_address: str,
    trading_provider: str,
    from_datetime: datetime.datetime,
    to_datetime: datetime.datetime,
) -> typing.List[typing.List]:
    trading_provider_client = factory.Factory.create(
        provider=src_enums.TradingProvider[trading_provider]
    )
    history_report = accountant.TradingAccountant(
        trading_data_provider=trading_provider_client
    ).get_order_history(
        wallet_address=wallet_address,
        from_datetime=from_datetime,
        to_datetime=to_datetime,
    )

    return [historical_order.to_list() for historical_order in history_report]


def get_position_fundings_report(
    wallet_address: str,
    trading_provider: str,
    from_datetime: datetime.datetime,
    to_datetime: datetime.datetime,
) -> typing.List[typing.List]:
    history_report = accountant.TradingAccountant(
        trading_data_provider=factory.Factory.create(
            provider=src_enums.TradingProvider[trading_provider]
        )
    ).get_position_fundings_history(
        wallet_address=wallet_address,
        from_datetime=from_datetime,
        to_datetime=to_datetime,
    )

    return [
        historical_position_funding.to_list()
        for historical_position_funding in history_report
    ]


def get_or_create_accounting_wallet(
    wallet_address: str, trading_provider: str
) -> src_models.AccountingWallet:
    trading_provider_enum = src_enums.TradingProvider[trading_provider]
    return src_models.AccountingWallet.objects.get_or_create(
        address=wallet_address,
        provider=trading_provider_enum.value,
        provider_name=trading_provider_enum.name,
    )
