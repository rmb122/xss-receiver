from __future__ import annotations

import asyncio
import dataclasses
import json
import multiprocessing
import os
import struct
import typing
from asyncio import StreamReader, StreamWriter

import sanic

from xss_receiver.asserts import aiopipe


def get_worker_num():
    try:
        worker_num = len(os.sched_getaffinity(0))
    except AttributeError:
        worker_num = os.cpu_count() or 1
    return worker_num


@dataclasses.dataclass
class PublishMessage:
    msg_type: int
    msg_content: object

    def to_json(self) -> str:
        return json.dumps(dataclasses.asdict(self))

    @staticmethod
    def from_json(input_str: str) -> PublishMessage:
        input_obj = json.loads(input_str)
        publish_msg = PublishMessage(msg_type=-1, msg_content='')
        publish_msg.msg_type = input_obj['msg_type']
        publish_msg.msg_content = input_obj['msg_content']
        return publish_msg


class PublishSubscribe:
    _worker_num: int
    _duplex_list: typing.List[aiopipe.AioDuplex]

    _opened_txs: typing.List[StreamWriter]
    _opened_rx: StreamReader
    _opened = False

    _before_process_num = 2  # Sanic 本身自己的 Main process 和 Config 里面的 multiprocessing.Manager
    _callbacks: typing.Dict[int, typing.Callable] = {}

    def __init__(self):
        self._duplex_list = []
        self._opened_txs = []
        self._worker_num = get_worker_num()

        if self._worker_num > 1 and os.name != "posix":
            self._worker_num = 1

        for duplex in aiopipe.aioduplex(self._worker_num):
            duplex.detach()
            self._duplex_list.append(duplex)

    def opened(self):
        return self._opened

    def register_callback(self, msg_type, func):
        self._callbacks[msg_type] = func

    async def open_pipes(self):
        if not self.opened() and self._worker_num > 1:
            identity, = multiprocessing.current_process()._identity
            self._opened_rx = await self._duplex_list[identity - self._before_process_num].open_rx()
            self._opened_txs = [await i.open_tx() for i in self._duplex_list]
        else:
            self._opened_rx = await self._duplex_list[0].open_rx()
            self._opened_txs = [await self._duplex_list[0].open_tx()]

    async def subscribe(self):
        while True:
            length_bytes = await self._opened_rx.read(4)
            length, = struct.unpack('>I', length_bytes)

            payload = await self._opened_rx.read(length)
            msg = PublishMessage.from_json(payload.decode())

            if msg.msg_type in self._callbacks:
                asyncio.create_task(self._callbacks[msg.msg_type](msg))

    async def publish(self, data: PublishMessage):
        data = data.to_json()
        data = data.encode()
        for tx in self._opened_txs:
            length = len(data)
            length_bytes = struct.pack('>I', length)

            tx.write(length_bytes)
            tx.write(data)


def register_publish_subscribe(app: sanic.Sanic, publish_subscribe: PublishSubscribe):
    @app.before_server_start
    async def websocket_dispatch(*args):
        await publish_subscribe.open_pipes()
        asyncio.create_task(publish_subscribe.subscribe())
