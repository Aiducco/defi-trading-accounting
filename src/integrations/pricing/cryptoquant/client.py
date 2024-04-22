import logging
import typing
import datetime
from urllib import parse as url_parser

import requests
import simplejson
from django.conf import settings

from common import enums as common_enums
from common import utils as common_utils
from src.integrations.pricing.cryptoquant import exceptions

logger = logging.getLogger(__name__)


class CryptoQuantApiClient(object):
    API_BASE_URL = settings.CRYPTO_QUANT_API_BASE_URL
    API_KEY = settings.CRYPTO_QUANT_API_KEY
    VALID_STATUS_CODES = [200]

    LOG_PREFIX = "[CRYPTO-QUANT-API-CLIENT]"

    @property
    def api_key(self) -> str:
        return self.API_KEY

    def get_price(self, currency: str, from_datetime: datetime.datetime, to_datetime: datetime.datetime) -> float:
        from_datetime = from_datetime.astimezone(datetime.timezone.utc)
        from_datetime = from_datetime.strftime('%Y%m%dT%H%M%S')

        to_datetime = to_datetime.astimezone(datetime.timezone.utc)
        to_datetime = to_datetime.strftime('%Y%m%dT%H%M%S')

        params = {
            'window': 'min',
            'exchange': 'binance',
            'from': from_datetime,
            'to': to_datetime,
        }
        return self._get_response_data(
            response=self._request(
                endpoint='{}/market-data/price-ohlcv'.format(currency),
                params=params,
                method=common_enums.HttpMethod.GET,
            )
        )['result']['data'][0]['high']

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
                headers={
                    'Authorization': 'Bearer {}'.format(self.api_key),
                }
            )

            if response.status_code not in self.VALID_STATUS_CODES:
                msg = "Invalid API client response (status_code={}, data={})".format(
                    response.status_code,
                    response.content.decode(encoding="utf-8"),
                )
                logger.error("{} {}.".format(self.LOG_PREFIX, msg))
                raise exceptions.CryptoQuantAPIBadResponseCodeError(
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
            raise exceptions.CryptoQuantAPIException(msg)
        except requests.RequestException as e:
            msg = "Request exception. Error: {}".format(
                common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.LOG_PREFIX, msg))
            raise exceptions.CryptoQuantAPIException(msg)

        return response

    @staticmethod
    def _get_response_data(
        response: requests.Response,
    ) -> typing.Union[dict, typing.List[dict]]:
        return simplejson.loads(response.content)

    def _get_payload_with_credentials(self, payload: typing.Optional[dict]) -> dict:
        payload = payload if payload else {}
        return payload | {"api_key": self.api_key}
