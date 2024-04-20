import base64
import datetime
import hashlib
import hmac
import json
import logging
import typing
from urllib import parse as url_parser

import requests
import simplejson
from django.conf import settings

from common import enums as common_enums
from common import utils as common_utils
from src.integrations.trading.gateways.dydx import exceptions

logger = logging.getLogger(__name__)


class DYDXApiClient(object):
    API_BASE_URL = settings.DYDX_API_BASE_URL
    API_CREDENTIALS = settings.DYDX_CREDENTIALS
    VALID_STATUS_CODES = [200]

    LOG_PREFIX = "[DYDX-API-CLIENT]"

    def __init__(self, wallet_address: str) -> None:
        self.wallet_address = wallet_address

    @property
    def wallet_credentials(self) -> typing.Dict:
        return self.API_CREDENTIALS[self.wallet_address]

    @property
    def api_key(self) -> str:
        return self.wallet_credentials["key"]

    @property
    def api_secret(self) -> str:
        return self.wallet_credentials["secret"]

    @property
    def api_passphrase(self) -> str:
        return self.wallet_credentials["passphrase"]

    @property
    def account_id(self) -> str:
        return self.wallet_credentials["account_id"]

    def get_positions(
        self, limit: int = 100, pages: int = 1
    ) -> typing.List[typing.Dict]:
        return self._get_paginated_response(
            endpoint="/v3/positions",
            method=common_enums.HttpMethod.GET,
            params={},
            data_field="positions",
            pagination_field="createdAt",
            limit=limit,
            pages=pages,
        )

    def get_orders(self, limit: int = 100, pages: int = 1) -> typing.List[typing.Dict]:
        return self._get_paginated_response(
            endpoint="/v3/orders",
            method=common_enums.HttpMethod.GET,
            params={"returnLatestOrders": "true"},
            data_field="orders",
            pagination_field="createdAt",
            limit=limit,
            pages=pages,
        )

    def get_order_fills(
        self, limit: int = 100, pages: int = 2
    ) -> typing.List[typing.Dict]:
        return self._get_paginated_response(
            endpoint="/v3/fills",
            method=common_enums.HttpMethod.GET,
            params={},
            data_field="fills",
            pagination_field="createdAt",
            limit=limit,
            pages=pages,
        )

    def get_funding_payments(
        self,
        limit: int = 100,
        pages: int = 1,
        to_datetime: typing.Optional[datetime.datetime] = None,
    ) -> typing.List[typing.Dict]:
        params = {}
        if to_datetime:
            params["effectiveBeforeOrAt"] = to_datetime.isoformat()

        return self._get_paginated_response(
            endpoint="/v3/funding",
            method=common_enums.HttpMethod.GET,
            params=params,
            data_field="fundingPayments",
            pagination_field="effectiveAt",
            limit=limit,
            pages=pages,
        )

    def get_order(self, order_id: str) -> typing.Dict:
        return self._get_response_data(
            response=self._request(
                endpoint="/v3/orders/{}".format(order_id),
                method=common_enums.HttpMethod.GET,
            )
        )["order"]

    def get_account(self) -> typing.Dict:
        return self._get_response_data(
            response=self._request(
                endpoint="/v3/accounts/{}".format(self.account_id),
                method=common_enums.HttpMethod.GET,
                params={"ethereumAddress": self.wallet_address},
            )
        )["account"]

    def get_markets(
        self,
        market: typing.Optional[str] = None,
    ) -> typing.Dict:
        params = {}
        if market:
            params["market"] = market

        return self._get_response_data(
            response=self._request(
                endpoint="/v3/markets",
                method=common_enums.HttpMethod.GET,
                params=params,
            )
        )["markets"]

    def _get_paginated_response(
        self,
        endpoint: str,
        method: common_enums.HttpMethod,
        params: typing.Dict,
        data_field: str,
        pagination_field: str,
        limit: int = 100,
        pages: int = 1,
    ) -> typing.List:
        params.update({"limit": limit})
        paginated_data = []
        current_page = 0
        while True:
            data = self._get_response_data(
                response=self._request(
                    endpoint=endpoint,
                    method=method,
                    params=params,
                )
            )
            payload_data = data.get(data_field, [])
            if not payload_data:
                break

            paginated_data.extend(payload_data)
            params["createdBeforeOrAt"] = payload_data[-1][pagination_field]

            current_page += 1
            if current_page >= pages:
                break

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
            current_timestamp = self._get_current_iso_datetime()
            response = requests.request(
                url=url,
                method=method.value,
                params=params,
                json=payload,
                headers={
                    # "Content-Type": "application/json",
                    "DYDX-SIGNATURE": self._get_signature(
                        request_url=self._get_endpoint_with_params(
                            endpoint=endpoint, params=params
                        ),
                        method=method.name,
                        timestamp=current_timestamp,
                        payload=payload,
                    ),
                    "DYDX-API-KEY": self.api_key,
                    "DYDX-TIMESTAMP": current_timestamp,
                    "DYDX-PASSPHRASE": self.api_passphrase,
                },
            )

            if response.status_code not in self.VALID_STATUS_CODES:
                msg = "Invalid API client response (status_code={}, data={})".format(
                    response.status_code,
                    response.content.decode(encoding="utf-8"),
                )
                logger.error("{} {}.".format(self.LOG_PREFIX, msg))
                raise exceptions.DYDXAPIBadResponseCodeError(
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
            raise exceptions.DYDXAPIException(msg)
        except requests.RequestException as e:
            msg = "Request exception. Error: {}".format(
                common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.LOG_PREFIX, msg))
            raise exceptions.DYDXAPIException(msg)

        return response

    def _get_signature(
        self,
        request_url: str,
        method: str,
        timestamp: str,
        payload: typing.Optional[typing.Dict],
    ) -> str:
        message_string = (
            timestamp + method + request_url + (json.dumps(payload) if payload else "")
        )

        hashed = hmac.new(
            base64.urlsafe_b64decode(
                self.api_secret.encode("utf-8"),
            ),
            msg=message_string.encode("utf-8"),
            digestmod=hashlib.sha256,
        )
        return base64.urlsafe_b64encode(hashed.digest()).decode()

    @staticmethod
    def _get_current_iso_datetime() -> str:
        return (
            datetime.datetime.utcnow().strftime(
                "%Y-%m-%dT%H:%M:%S.%f",
            )[:-3]
            + "Z"
        )

    @staticmethod
    def _get_response_data(
        response: requests.Response,
    ) -> typing.Union[typing.Dict, typing.List[typing.Dict]]:
        return simplejson.loads(response.content)

    @staticmethod
    def _get_endpoint_with_params(
        endpoint: str, params: typing.Optional[typing.Dict]
    ) -> str:
        if not params:
            return endpoint

        return endpoint + "?" + url_parser.urlencode(query=params)
