class TradingProviderClientError(Exception):
    pass


class TradingProviderApiClientError(TradingProviderClientError):
    pass


class DataValidationError(TradingProviderClientError):
    pass


class TradingProviderNotSupportedError(TradingProviderClientError):
    pass


class PositionNotFoundError(TradingProviderClientError):
    pass


class TradingAccountantServiceError(Exception):
    pass


class AccountingWalletNotFoundError(TradingAccountantServiceError):
    pass
