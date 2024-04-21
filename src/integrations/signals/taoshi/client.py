import logging
import typing
from urllib import parse as url_parser

import requests
import simplejson
from django.conf import settings

from common import enums as common_enums
from common import utils as common_utils
from src.integrations.signals.taoshi import exceptions

logger = logging.getLogger(__name__)


class TaoshiApiClient(object):
    API_BASE_URL = settings.TAOSHI_API_BASE_URL
    API_KEY = settings.TAOSHI_API_KEY
    VALID_STATUS_CODES = [200]

    LOG_PREFIX = "[TAOSHI-API-CLIENT]"

    @property
    def api_key(self) -> str:
        return self.API_KEY

    def get_positions(self) -> dict:
        return self._get_response_data(
            response=self._request(
                endpoint="/validator-checkpoint",
                method=common_enums.HttpMethod.GET,
            )
        )["positions"]

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
                json=self._get_payload_with_credentials(payload=payload),
            )

            if response.status_code not in self.VALID_STATUS_CODES:
                msg = "Invalid API client response (status_code={}, data={})".format(
                    response.status_code,
                    response.content.decode(encoding="utf-8"),
                )
                logger.error("{} {}.".format(self.LOG_PREFIX, msg))
                raise exceptions.TaoshiAPIBadResponseCodeError(
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
            raise exceptions.TaoshiAPIException(msg)
        except requests.RequestException as e:
            msg = "Request exception. Error: {}".format(
                common_utils.get_exception_message(exception=e)
            )
            logger.exception("{} {}.".format(self.LOG_PREFIX, msg))
            raise exceptions.TaoshiAPIException(msg)

        return response

    @staticmethod
    def _get_response_data(
        response: requests.Response,
    ) -> typing.Union[dict, typing.List[dict]]:
        return simplejson.loads(response.content)

    def _get_payload_with_credentials(self, payload: typing.Optional[dict]) -> dict:
        payload = payload if payload else {}
        return payload | {"api_key": self.api_key}
