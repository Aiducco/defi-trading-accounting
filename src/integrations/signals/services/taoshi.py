import datetime
import logging
import typing

from django.db import transaction
from django.utils import timezone

from common import utils as common_utils
from src import constants as src_constants
from src import models as src_models
from src.integrations.pricing.cryptoquant import client as cryptoquant_client
from src.integrations.signals.taoshi import client as taoshi_api_client

logger = logging.getLogger(__name__)

_LOG_PREFIX = "[TAOSHI-SERVICES]"


def import_taoshi_positions() -> None:
    logger.info(
        "{} Started importing taoshi position data.".format(
            _LOG_PREFIX
        )
    )
    positions = _get_taoshi_positions()
    if not positions:
        return

    logger.info(
        "{} Found total {} miners positions to check for importing.".format(
            _LOG_PREFIX, len(positions)
        )
    )

    for miner_positions in positions:
        for position in positions[miner_positions]['positions']:
            try:
                if not _is_position_valid(position=position):
                    continue

                _import_taoshi_position(position=position)
            except Exception as e:
                logger.exception(
                    "{} Unable to import taoshi position (position_id={}). Error: {}. Continue.".format(
                        _LOG_PREFIX,
                        position["position_uuid"],
                        common_utils.get_exception_message(exception=e),
                    )
                )
                continue

    logger.info(
        "{} Finished importing taoshi position data.".format(
            _LOG_PREFIX,
        )
    )


def _get_taoshi_positions() -> typing.Optional[dict]:
    try:
        return taoshi_api_client.TaoshiApiClient().get_positions()
    except Exception as e:
        logger.exception(
            "{} Unable to get taoshi positions. Error: {}.".format(
                _LOG_PREFIX,
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


def _import_taoshi_position(position: dict) -> None:
    logger.info(
        "{} Importing position (position_id={}).".format(
            _LOG_PREFIX, position["position_uuid"]
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
                'market_price': _get_market_price(currency=base_currency.lower(), from_datetime=timezone.datetime.fromtimestamp(
                    order_info["processed_ms"] / 1000
                ), to_datetime=timezone.datetime.fromtimestamp(
                    order_info["processed_ms"] / 1000
                )),
                "position": taoshi_position,
            }

            src_models.TaoshiPositionOrder.objects.update_or_create(
                order_uuid=order_info["order_uuid"], defaults=order_data
            )

    logger.info(
        "{} Imported position (id={},position_id={}).".format(
            _LOG_PREFIX, taoshi_position.id, position["position_uuid"]
        )
    )


def _get_market_price(currency: str, from_datetime: datetime.datetime, to_datetime: datetime.datetime) -> float:
    try:
        return cryptoquant_client.CryptoQuantApiClient().get_price(currency=currency, from_datetime=from_datetime, to_datetime=to_datetime)
    except Exception as e:
        logger.exception(
            "{} Unable to get market price (currency={}) positions. Error: {}.".format(
                _LOG_PREFIX,
                currency,
                common_utils.get_exception_message(exception=e),
            )
        )
        return 0.0
