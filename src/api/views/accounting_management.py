import dataclasses
import datetime
import logging
import typing

import simplejson
from django import http, views

from common import utils as common_utils
from src.api import schemas as api_schemas
from src.integrations.trading.providers.services import (
    trading_provider as trading_provider_services,
)

logger = logging.getLogger(__name__)

_LOG_PREFIX = "[ACCOUNTING-MANAGEMENT-VIEW]"


class AccountingWallet(views.View):
    def post(
        self, request: http.HttpRequest, *args: typing.Any, **kwargs: typing.Any
    ) -> http.HttpResponse:
        try:
            payload = simplejson.loads(request.body.decode("utf-8"))
        except Exception:
            return http.HttpResponse(
                headers={"Content-Type": "application/json"},
                content=simplejson.dumps({"error": {"title": "Payload is not valid."}}),
                status=400,
            )

        logger.info(
            "{} Received wallet address to save (payload={}).".format(
                _LOG_PREFIX, payload
            )
        )

        validated_data = common_utils.validate_data_schema(
            data=payload, schema=api_schemas.WalletAddressDataSchema()
        )
        if not validated_data:
            return http.HttpResponse(
                headers={"Content-Type": "application/json"},
                content=simplejson.dumps({"error": {"title": "Payload is not valid."}}),
                status=400,
            )

        try:
            trading_provider_services.get_or_create_accounting_wallet(
                wallet_address=validated_data["address"],
                trading_provider=validated_data["provider"],
            )
        except Exception as e:
            logger.exception(
                "{} Unexpected exception occurred while saving accounting wallet. Error: {}".format(
                    _LOG_PREFIX, common_utils.get_exception_message(exception=e)
                )
            )
            return http.HttpResponse(
                headers={"Content-Type": "application/json"},
                content=simplejson.dumps({"error": {"title": "Internal server error"}}),
                status=500,
            )

        logger.info(
            "{} Successfully processed and saved accounting wallet (payload={}).".format(
                _LOG_PREFIX, validated_data
            )
        )
        return http.HttpResponse(
            headers={"Content-Type": "application/json"},
            content=simplejson.dumps({"data": {"attributes": payload}}),
            status=201,
        )
