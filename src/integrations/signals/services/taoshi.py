import logging
import typing

from django.db import transaction
from django.utils import timezone

from common import utils as common_utils
from src import enums as src_enums
from src import constants as src_constants
from src import models as src_models
from src.integrations.signals.taoshi import client as taoshi_api_client

logger = logging.getLogger(__name__)

_LOG_PREFIX = "[TAOSHI-SERVICES]"


def import_taoshi_positions(miner: src_enums.TaoshiMiner) -> None:
    logger.info(
        "{} Started importing taoshi position data (miner={}, public_key={}).".format(
            _LOG_PREFIX,
            miner.name,
            src_constants.TAOSHI_MINER_CONFIG[miner.name]["public_key"],
        )
    )
    positions = _get_taoshi_positions(miner=miner)
    if not positions:
        return

    logger.info(
        "{} Found total {} positions to check for importing (miner={}).".format(
            _LOG_PREFIX, len(positions), miner.name
        )
    )

    for position in positions:
        try:
            if not _is_position_valid(position=position):
                continue

            _import_taoshi_position(position=position, miner=miner)
        except Exception as e:
            logger.exception(
                "{} Unable to import taoshi position (miner={}, position_id={}). Error: {}. Continue.".format(
                    _LOG_PREFIX,
                    miner.name,
                    position["position_uuid"],
                    common_utils.get_exception_message(exception=e),
                )
            )
            continue

    logger.info(
        "{} Finished importing taoshi position data (miner={}, public_key={}).".format(
            _LOG_PREFIX,
            miner.name,
            src_constants.TAOSHI_MINER_CONFIG[miner.name]["public_key"],
        )
    )


def _get_taoshi_positions(miner: src_enums.TaoshiMiner) -> typing.Optional[typing.List[dict]]:
    try:
        return taoshi_api_client.TaoshiApiClient().get_positions()[
            src_constants.TAOSHI_MINER_CONFIG[miner.name]["public_key"]
        ]["positions"]
    except Exception as e:
        logger.exception(
            "{} Unable to get taoshi positions (miner={}, public_key={}). Error: {}.".format(
                _LOG_PREFIX,
                miner.name,
                src_constants.TAOSHI_MINER_CONFIG[miner.name]["public_key"],
                common_utils.get_exception_message(exception=e),
            )
        )
        return None


def _is_position_valid(position: dict) -> bool:
    base_currency, counter_currency = position["trade_pair"][1].split("/")
    if (
        base_currency in src_constants.TAOSHI_ALLOWED_TRADING_CURRENCIES
        or counter_currency in src_constants.TAOSHI_ALLOWED_TRADING_CURRENCIES
    ):
        return True

    return False


def _import_taoshi_position(miner: src_enums.TaoshiMiner, position: dict) -> None:
    logger.info(
        "{} Importing position (miner={}, position_id={}).".format(
            _LOG_PREFIX, miner.name, position["position_uuid"]
        )
    )
    base_currency, counter_currency = position["trade_pair"][1].split("/")
    with transaction.atomic():
        position_data = {
            "position_uuid": position["position_uuid"],
            "average_entry_price": position["average_entry_price"],
            "close_time": timezone.datetime.fromtimestamp(position["close_ms"] / 1000)
            if position["is_closed_position"]
            else None,
            "open_time": timezone.datetime.fromtimestamp(position["open_ms"] / 1000),
            "current_return": position["current_return"],
            "initial_entry_price": position["initial_entry_price"],
            "is_closed": position["is_closed_position"],
            "net_leverage": position["net_leverage"],
            "miner": miner.value,
            "miner_name": miner.name,
            "miner_public_key": position['miner_hotkey'],
            "position_type": position["position_type"],
            "return_at_close": position["return_at_close"],
            "base_currency": base_currency,
            "counter_currency": counter_currency,
        }

        taoshi_position, created = src_models.TaoshiPosition.objects.update_or_create(
            position_uuid=position["position_uuid"], defaults=position_data
        )

        for order_info in position["orders"]:
            order_data = {
                "order_uuid": order_info["order_uuid"],
                "leverage": order_info["leverage"],
                "processed_time": timezone.datetime.fromtimestamp(
                    order_info["processed_ms"] / 1000
                ),
                "order_type": order_info["order_type"],
                "price": order_info["price"],
                "position": taoshi_position,
            }

            src_models.TaoshiPositionOrder.objects.update_or_create(
                order_uuid=order_info["order_uuid"], defaults=order_data
            )

    logger.info(
        "{} Imported position (id={}, miner={}, position_id={}).".format(
            _LOG_PREFIX, taoshi_position.id, miner.name, position["position_uuid"]
        )
    )
