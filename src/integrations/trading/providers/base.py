import abc
import datetime
import typing

from src import enums as src_enums
from src import models as src_models
from src.integrations.trading.providers import messages as trading_messages


class BaseProvider(object):
    @property
    @abc.abstractmethod
    def provider(self) -> src_enums.TradingProvider:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def api_client_class(self) -> typing.Type[typing.Callable]:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def order_open_statuses(self) -> typing.List[int]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_order_fills(
        self,
        wallet_address: str,
        from_datetime: datetime.datetime,
        to_datetime: datetime.datetime,
    ) -> typing.List[trading_messages.OrderFill]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_order(self, wallet_address: str, order_id: str) -> trading_messages.Order:
        raise NotImplementedError

    @abc.abstractmethod
    def get_open_order_ids(self, wallet_address: str) -> typing.List[str]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_positions(
        self,
        wallet_address: str,
        from_datetime: datetime.datetime,
        to_datetime: datetime.datetime,
    ) -> typing.List[trading_messages.Position]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_position_fundings(
        self,
        wallet_address: str,
        from_datetime: datetime.datetime,
        to_datetime: typing.Optional[datetime.datetime] = None,
    ) -> typing.List[trading_messages.PositionFunding]:
        raise NotImplementedError

    @abc.abstractmethod
    def prepare_order_fill_for_import(
        self, order_fill: trading_messages.OrderFill, order: src_models.Order
    ) -> trading_messages.OrderFillImportData:
        raise NotImplementedError

    @abc.abstractmethod
    def get_account_portfolio(
        self, wallet_address: str
    ) -> trading_messages.WalletAccount:
        raise NotImplementedError
