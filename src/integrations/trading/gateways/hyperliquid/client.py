import datetime
import logging
import typing
from urllib import parse as url_parser

import requests
import simplejson
from django.conf import settings

from common import enums as common_enums
from common import utils as common_utils
from src.integrations.trading.gateways.hyperliquid import exceptions

logger = logging.getLogger(__name__)


class HyperLiquidApiClient(object):
    API_BASE_URL = settings.HYPERLIQUID_API_BASE_URL
    VALID_STATUS_CODES = [200]

    LOG_PREFIX = "[HYPER-LIQUID-API-CLIENT]"

    def get_open_orders(
        self, wallet_address: str, limit: int = 100, pages: int = 1
    ) -> typing.List[typing.Dict]:
        return self._get_paginated_data(
            endpoint="/info",
            method=common_enums.HttpMethod.POST,
            payload={"type": "openOrders", "user": wallet_address},
            pages=pages,
            limit=limit,
        )

    def get_order_fills(
        self, wallet_address: str, limit: int = 100, pages: int = 1
    ) -> typing.List[typing.Dict]:
        return self._get_paginated_data(
            endpoint="/info",
            method=common_enums.HttpMethod.POST,
            payload={"type": "userFills", "user": wallet_address},
            pages=pages,
            limit=limit,
        )

    def get_position_fundings(
        self,
        wallet_address: str,
        from_datetime: datetime.datetime,
        to_datetime: typing.Optional[datetime.datetime] = None,
        limit: int = 500,
        pages: int = 1,
    ) -> typing.List[typing.Dict]:
        payload = {
            "type": "userFunding",
            "user": wallet_address,
            "startTime": int(from_datetime.timestamp() * 1000),
        }

        if to_datetime:
            payload["endTime"] = int(to_datetime.timestamp() * 1000)

        # return self._get_paginated_data(
        #     endpoint="/info",
        #     method=common_enums.HttpMethod.POST,
        #     payload=payload,
        #     pages=pages,
        #     limit=limit,
        # )
        #
        return self._get_paginated_response(
            endpoint="/info",
            method=common_enums.HttpMethod.POST,
            payload=payload,
        )

    def get_order(self, wallet_address: str, order_id: int) -> typing.Dict:
        return self._get_response_data(
            response=self._request(
                endpoint="/info",
                method=common_enums.HttpMethod.POST,
                payload={
                    "type": "orderStatus",
                    "oid": order_id,
                    "user": wallet_address,
                },
            )
        )

    def get_positions(
        self,
        wallet_address: str,
        limit: int = 100,
        pages: int = 1,
    ) -> typing.List[typing.Dict]:
        return self._get_paginated_data(
            endpoint="/info",
            method=common_enums.HttpMethod.POST,
            payload={"type": "clearinghouseState", "user": wallet_address},
            pages=pages,
            limit=limit,
            data_field="assetPositions",
        )

    def get_account(self, wallet_address: str) -> typing.Dict:
        return self._get_response_data(
            response=self._request(
                endpoint="/info",
                method=common_enums.HttpMethod.POST,
                payload={"type": "clearinghouseState", "user": wallet_address},
            )
        )["marginSummary"]

    def _get_paginated_data(
        self,
        endpoint: str,
        method: common_enums.HttpMethod.POST,
        payload: typing.Dict,
        data_field: typing.Optional[str] = None,
        limit: int = 50,
        pages: int = 1,
    ) -> typing.List[typing.Dict]:
        response_data = self._get_response_data(
            response=self._request(
                endpoint=endpoint,
                method=method,
                payload=payload,
            )
        )

        if data_field:
            response_data = response_data[data_field]

        return response_data[: limit * pages]

    @staticmethod
    def _get_response_data(
        response: requests.Response,
    ) -> typing.Union[typing.Dict, typing.List[typing.Dict]]:
        return simplejson.loads(response.content)

    def _get_paginated_response(
        self,
        endpoint: str,
        method: common_enums.HttpMethod,
        payload: typing.Dict,
    ) -> typing.List:
        paginated_data = []
        while True:
            data = self._get_response_data(
                response=self._request(
                    endpoint=endpoint,
                    method=method,
                    payload=payload,
                )
            )
            paginated_data.extend(data)

            if not data or len(data) == 1:
                break

            payload["startTime"] = data[-1]["time"]

        return paginated_data

    def _request(
        self,
        endpoint: str,
        method: common_enums.HttpMethod,
        params: typing.Optional[dict] = None,
        payload: typing.Optional[dict] = None,
    ) -> requests.Response:
        url = url_parser.urljoin(base=self.API_BASE_URL, url=endpoint)
        try:
            response = requests.request(
                url=url,
                method=method.value,
                params=params,
                json=payload,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code not in self.VALID_STATUS_CODES:
                msg = "Invalid API client response (status_code={}, data={})".format(
                    response.status_code,
                    response.content.decode(encoding="utf-8"),
                )
                logger.error("{} {}.".format(self.LOG_PREFIX, msg))
                raise exceptions.HyperLiquidAPIBadResponseCodeError(
                    message=msg, code=response.status_code
                )

            logger.debug(
                "{} Successful response (endpoint={}, status_code={}, payload={}, params={}, raw_response={}).".format(
                    self.LOG_PREFIX,
                    endpoint,
                    response.status_code,
                    payload,
                    params,
                    response.content.decode(encoding="utf-8"),
                )
            )
        except requests.exceptions.ConnectTimeout as e:
            msg = "Connect timeout. Error: {}".format(
                common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.LOG_PREFIX, msg))
            raise exceptions.HyperLiquidAPIException(msg)
        except requests.RequestException as e:
            msg = "Request exception. Error: {}".format(
                common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.LOG_PREFIX, msg))
            raise exceptions.HyperLiquidAPIException(msg)

        return response
