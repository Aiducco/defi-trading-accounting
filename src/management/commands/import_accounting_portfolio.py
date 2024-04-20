import datetime
import logging
import typing

from django.core.management.base import BaseCommand, CommandParser

from common import utils as common_utils
from src import enums, models
from src.integrations.trading.providers import factory as trading_provider_factory
from src.integrations.trading.providers.services import (
    importer as trading_data_importer,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
            Imports all accounting wallet portfolios for all wallet addresses in accounting_wallet.
            ex. python manage.py import_accounting_portfolio --provider=HYPERLIQUID
            """

    log_prefix = "[IMPORT-ACCOUNTING-PORTFOLIO]"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--provider",
            required=True,
            type=str,
            choices=[
                trading_provider.name for trading_provider in enums.TradingProvider
            ],
            help="One of trading providers specified in TradingProvider enum.",
        )

    def handle(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        logger.info(
            "{} Started command '{}' (provider={}).".format(
                self.log_prefix, __name__.split(".")[-1], kwargs["provider"]
            )
        )

        trading_provider = enums.TradingProvider[kwargs["provider"]]
        accounting_wallets = models.AccountingWallet.objects.filter(
            provider=trading_provider.value
        )

        if not accounting_wallets:
            logger.info(
                "{} No accounting wallets to import portfolios for. Exiting.".format(
                    self.log_prefix
                )
            )
            return

        logger.info(
            "{} Found {} accounting wallets to import portfolios for.".format(
                self.log_prefix, len(accounting_wallets)
            )
        )

        for accounting_wallet in accounting_wallets:
            logger.info(
                "{} Importing account portfolios data (wallet_address={}, accounting_wallet_id={}).".format(
                    self.log_prefix, accounting_wallet.address, accounting_wallet.id
                )
            )
            try:
                trading_data_importer.TradingDataImporter(
                    trading_data_provider=trading_provider_factory.Factory.create(
                        provider=trading_provider
                    )
                ).import_wallet_portfolio(wallet_address=accounting_wallet.address)
            except Exception as e:
                logger.exception(
                    "{} Unexpected exception occurred while importing account portfolios data. Error: {}.".format(
                        self.log_prefix,
                        common_utils.get_exception_message(exception=e),
                    )
                )

        logger.info(
            "{} Finished command '{}' (provider={}).".format(
                self.log_prefix, __name__.split(".")[-1], kwargs["provider"]
            )
        )
