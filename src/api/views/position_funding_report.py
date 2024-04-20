import dataclasses
import datetime
import logging
import typing

import simplejson
from django import http, views

from common import exceptions as common_exceptions
from common import utils as common_utils
from src.api import schemas as api_schemas
from src.integrations.trading.providers import messages as provider_messages
from src.integrations.trading.providers.services import (
    trading_provider as trading_provider_services,
)

logger = logging.getLogger(__name__)

_LOG_PREFIX = "[POSITION-FUNDING-REPORT-VIEW]"


class PositionFundingsReport(views.View):
    def get(
        self, request: http.HttpRequest, *args: typing.Any, **kwargs: typing.Any
    ) -> http.HttpResponse:
        logger.info("{} Generating position funding report.".format(_LOG_PREFIX))
        try:
            validated_query_params = common_utils.validate_data_schema(
                data=request.GET, schema=api_schemas.PositionFundingExportQuerySchema()
            )
        except common_exceptions.ValidationSchemaException as e:
            logger.exception(
                "{} Unable to validate query parameters (query_parameters={}). Error: {}.".format(
                    _LOG_PREFIX,
                    dict(request.GET),
                    common_utils.get_exception_message(exception=e),
                )
            )
            return http.HttpResponse(
                headers={"Content-Type": "application/json"},
                content=simplejson.dumps(
                    {
                        "error": {
                            "title": "Invalid query parameters: {}".format(
                                common_utils.get_exception_message(exception=e)
                            )
                        }
                    }
                ),
                status=400,
            )

        logger.info(
            "{} Generating position funding report (wallet_address={}, provider={}, from_datetime={}, to_datetime={}).".format(
                _LOG_PREFIX,
                validated_query_params["wallet_address"],
                validated_query_params["provider"],
                validated_query_params["from_date"],
                validated_query_params["to_date"],
            )
        )

        from_date = validated_query_params["from_date"]
        to_date = validated_query_params["to_date"]
        try:
            report = trading_provider_services.get_position_fundings_report(
                wallet_address=validated_query_params["wallet_address"],
                trading_provider=validated_query_params["provider"],
                from_datetime=datetime.datetime(
                    from_date.year, from_date.month, from_date.day
                ),
                to_datetime=datetime.datetime(to_date.year, to_date.month, to_date.day),
            )
        except Exception as e:
            logger.exception(
                "{} Unexpected exception while generating position funding history report (wallet_address={}, provider={}, from_datetime={}, to_datetime={}). Error: {}.".format(
                    _LOG_PREFIX,
                    validated_query_params["wallet_address"],
                    validated_query_params["provider"],
                    from_date,
                    to_date,
                    common_utils.get_exception_message(exception=e),
                )
            )
            return http.HttpResponse(
                headers={"Content-Type": "application/json"},
                content=simplejson.dumps({"error": {"title": "Internal server error"}}),
                status=500,
            )

        return http.HttpResponse(
            headers={
                "Content-Type": "text/csv",
                "Content-Disposition": "attachment; filename=position_funding_history_{}_{}_{}_{}.csv".format(
                    validated_query_params["provider"],
                    validated_query_params["wallet_address"],
                    from_date,
                    to_date,
                ),
            },
            content=common_utils.get_csv_file_writer(
                headers=[
                    field.name
                    for field in dataclasses.fields(
                        provider_messages.PositionFundingHistory
                    )
                ],  # TODO: Chenge this up to be properly handled
                data=report,
            ),
            status=200,
        )
