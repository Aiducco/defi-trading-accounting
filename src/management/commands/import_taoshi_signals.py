import logging
import typing

from django.core.management.base import BaseCommand

from common import utils as common_utils
from src import enums
from src.integrations.signals.services import taoshi as taoshi_services

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
            Imports all positions for all supported taoshi miners.
            ex. python manage.py import_taoshi_signals
            """

    log_prefix = "[IMPORT-TAOSHI-SIGNALS]"

    def handle(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        logger.info(
            "{} Started command '{}'.".format(self.log_prefix, __name__.split(".")[-1])
        )

        for miner in enums.TaoshiMiner:
            logger.info(
                "{} Importing signals data (miner={}).".format(
                    self.log_prefix, miner.name
                )
            )

            try:
                taoshi_services.import_taoshi_positions(
                    miner=miner,
                )
            except Exception as e:
                logger.exception(
                    "{} Unexpected exception occurred while importing signals data (miner={}). Error: {}.".format(
                        self.log_prefix,
                        miner.name,
                        common_utils.get_exception_message(exception=e),
                    )
                )

            logger.info(
                "{} Finished importing signals data (miner={}).".format(
                    self.log_prefix, miner.name
                )
            )

        logger.info(
            "{} Finished command '{}'.".format(self.log_prefix, __name__.split(".")[-1])
        )
