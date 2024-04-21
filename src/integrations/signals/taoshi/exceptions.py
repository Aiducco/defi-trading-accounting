class TaoshiAPIException(Exception):
    pass


class TaoshiAPIBadResponseCodeError(TaoshiAPIException):
    def __init__(self, message: str, code: int) -> None:
        TaoshiAPIException.__init__(self)
        self.message = message
        self.code = code
