class CryptoQuantAPIException(Exception):
    pass


class CryptoQuantAPIBadResponseCodeError(CryptoQuantAPIException):
    def __init__(self, message: str, code: int) -> None:
        CryptoQuantAPIException.__init__(self)
        self.message = message
        self.code = code
