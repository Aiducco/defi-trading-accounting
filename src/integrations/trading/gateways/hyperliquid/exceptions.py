class HyperLiquidAPIException(Exception):
    pass


class HyperLiquidAPIBadResponseCodeError(HyperLiquidAPIException):
    def __init__(self, message: str, code: int) -> None:
        HyperLiquidAPIException.__init__(self)
        self.message = message
        self.code = code
