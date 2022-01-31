import asyncio
import multiprocessing
import socket
import typing

import dnslib

from xss_receiver import publish_subscribe, constants
from xss_receiver.database import session_maker, AsyncSession
from xss_receiver.models import DNSLog
from xss_receiver.publish_subscribe import PublishMessage
from xss_receiver.utils import create_async_udp_socket


async def process_packet(packet_bytes: bytes, remote_addr: typing.Tuple[str, int]):
    session = session_maker()
    session: AsyncSession

    try:
        packet = dnslib.DNSRecord.parse(packet_bytes)
        if packet.header.opcode == 0:  # type == Query
            dns_log = DNSLog(client_ip=remote_addr[0], transaction_id=packet.header.id, domain=packet.q.qname.idna(), dns_type=packet.q.qtype, dns_class=packet.q.qclass)
            session.add(dns_log)
            await session.commit()

            publish_subscribe.publish(PublishMessage(msg_type=constants.PUBLISH_MESSAGE_TYPE_NEW_DNS_LOG, msg_content=packet.q.qname.idna()))
    except Exception as e:
        pass


async def start_listen_dns(addr: typing.Tuple[str, int] = ('0.0.0.0', 53)):
    await publish_subscribe.open_pipes(tx_only=True)

    if ':' in addr[0]:
        inner_sck = socket.socket(family=socket.AF_INET6, type=socket.SOCK_DGRAM)
    else:
        inner_sck = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

    inner_sck.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    inner_sck.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    inner_sck.bind(addr)

    sck = await create_async_udp_socket(sock=inner_sck)

    while True:
        data, remote_addr = await sck.recvfrom()
        asyncio.create_task(process_packet(data, remote_addr))


def fork_and_start_listen_dns(addr: typing.Tuple[str, int] = ('0.0.0.0', 53)):
    def _wrapper(addr: typing.Tuple[str, int] = ('0.0.0.0', 53)):
        asyncio.run(start_listen_dns(addr))

    mp = multiprocessing.get_context("fork")
    process = mp.Process(
        target=_wrapper,
        args=(addr,),
    )
    process.daemon = True
    process.start()
