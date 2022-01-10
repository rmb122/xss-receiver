import dataclasses
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
        return dataclasses.asdict(self)

    @staticmethod
    def failed(msg="", payload=None):
        self = Response()
        self.code = 201
        self.msg = msg
        self.payload = payload
        return dataclasses.asdict(self)

    @staticmethod
    def invalid(msg="", payload=None):
        self = Response()
        self.code = 400
        self.msg = msg
        self.payload = payload
        return dataclasses.asdict(self)


@dataclass
class PagedResponse:
    payload: list
    total_page: int
    curr_page: int
