import logging
import typing

from src import enums as src_enums
from src.integrations.trading.providers import exceptions as trading_provider_exceptions
from src.integrations.trading.providers.dydx import client as dydx_client
from src.integrations.trading.providers.hyperliquid import client as hyperliquid_client

logger = logging.getLogger(__name__)


class Factory(object):
    _TRADE_PROVIDER_IMPLEMENTATION_MAP = {
        src_enums.TradingProvider.HYPERLIQUID: hyperliquid_client.HyperLiquidProvider,
        src_enums.TradingProvider.DYDX: dydx_client.DyDxProvider,
    }
    _LOG_PREFIX = "[TRADING-PROVIDER-FACTORY]"

    @classmethod
    def create(
        cls, provider: src_enums.TradingProvider
    ) -> typing.Union[hyperliquid_client.HyperLiquidProvider]:
        if provider not in cls._TRADE_PROVIDER_IMPLEMENTATION_MAP:
            msg = "Provider {} is not supported".format(provider.name)
            logger.error("{} {}.".format(cls._LOG_PREFIX, msg))
            raise trading_provider_exceptions.TradingProviderNotSupportedError(msg)

        return cls._TRADE_PROVIDER_IMPLEMENTATION_MAP[provider]()
