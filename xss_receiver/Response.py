from dataclasses import dataclass


@dataclass
class Response:
    code: int = 200
    msg: str = ""
    payload: object = None

    @staticmethod
    def success(msg="", payload=None):
        self = Response()
        self.code = 200
        self.msg = msg
        self.payload = payload
        return self

    @staticmethod
    def failed(msg="", payload=None):
        self = Response()
        self.code = 201
        self.msg = msg
        self.payload = payload
        return self

    @staticmethod
    def invalid(msg="", payload=None):
        self = Response()
        self.code = 400
        self.msg = msg
        self.payload = payload
        return self


@dataclass
class PagedResponse:
    payload: list
    total_page: int
    curr_page: int
