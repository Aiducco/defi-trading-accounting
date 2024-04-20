class DYDXAPIException(Exception):
    pass


class DYDXAPIBadResponseCodeError(DYDXAPIException):
    def __init__(self, message: str, code: int) -> None:
        DYDXAPIException.__init__(self)
        self.message = message
        self.code = code
