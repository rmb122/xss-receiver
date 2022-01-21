import os
import typing
from asyncio import StreamReader, StreamWriter, StreamReaderProtocol, BaseTransport, \
    get_running_loop, sleep
from typing import Tuple, Any, List

__pdoc__ = {}


def aiopipe() -> Tuple["AioPipeReader", "AioPipeWriter"]:
    """
    Create a new simplex multiprocess communication pipe.
    Return the read end and write end, respectively.
    """

    rx, tx = os.pipe()
    return AioPipeReader(rx), AioPipeWriter(tx)


def aioduplex(num: int) -> List["AioDuplex"]:
    """
    Create a new duplex multiprocess communication pipe.
    Both returned pipes can write to and read from the other.
    """
    pipe_list = []
    for _ in range(num):
        rx, tx = aiopipe()
        pipe_list.append(AioDuplex(rx, tx))
    return pipe_list


class AioPipeStream:
    """
    Abstract class for pipe readers and writers.
    """

    __pdoc__["AioPipeStream.__init__"] = None
    __pdoc__["AioPipeStream.open"] = None

    def __init__(self, fd):
        self._fd = fd
        self.transport = None

    async def open(self) -> typing.Union["StreamReader", "StreamWriter"]:
        self.transport, stream = await self._open()
        return stream

    async def close(self):
        if self.transport is not None:
            try:
                self.transport.close()
            except OSError:
                pass
            await sleep(0)

    async def _open(self) -> Tuple[BaseTransport, Any]:
        raise NotImplementedError()

    def detach(self):
        os.set_inheritable(self._fd, True)

    def __del__(self):
        try:
            os.close(self._fd)
        except OSError:
            pass


class AioPipeReader(AioPipeStream):
    """
    The read end of a pipe.
    """

    __pdoc__["AioPipeReader.__init__"] = None
    __pdoc__["AioPipeReader.open"] = """
        Open the receive end on the current event loop.
        This returns an async context manager, which must be used as part of an `async
        with` context. When the context is entered, the receive end is opened and an
        instance of [`StreamReader`][stdlib] is returned as the context variable. When the
        context is exited, the receive end is closed.
        [stdlib]: https://docs.python.org/3/library/asyncio-stream.html#asyncio.StreamReader
    """

    async def _open(self):
        rx = StreamReader()
        transport, _ = await get_running_loop().connect_read_pipe(
            lambda: StreamReaderProtocol(rx),
            os.fdopen(self._fd, 'rb'))

        return transport, rx


class AioPipeWriter(AioPipeStream):
    """
    The write end of a pipe.
    """

    __pdoc__["AioPipeWriter.__init__"] = None
    __pdoc__["AioPipeWriter.open"] = """
        Open the transmit end on the current event loop.
        This returns an async context manager, which must be used as part of an `async
        with` context. When the context is entered, the transmit end is opened and an
        instance of [`StreamWriter`][stdlib] is returned as the context variable. When the
        context is exited, the transmit end is closed.
        [stdlib]: https://docs.python.org/3/library/asyncio-stream.html#asyncio.StreamWriter
    """

    async def _open(self):
        rx = StreamReader()
        transport, proto = await get_running_loop().connect_write_pipe(
            lambda: StreamReaderProtocol(rx),
            os.fdopen(self._fd, "wb"))
        tx = StreamWriter(transport, proto, rx, get_running_loop())

        return transport, tx


class AioDuplex:
    """
    Represents one end of a duplex pipe.
    """

    __pdoc__["AioDuplex.__init__"] = None

    def __init__(self, rx: AioPipeReader, tx: AioPipeWriter):
        self._rx = rx
        self._tx = tx

    def detach(self):
        self._rx.detach()
        self._tx.detach()

    async def open_rx(self) -> "StreamReader":
        return await self._rx.open()

    async def open_tx(self) -> "StreamWriter":
        return await self._tx.open()
