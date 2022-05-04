import asyncio
import multiprocessing
import socket
import typing
import pylru
import dnslib
import re

from xss_receiver import publish_subscribe, constants, system_config
from xss_receiver.database import session_maker, AsyncSession
from xss_receiver.models import DNSLog
from xss_receiver.publish_subscribe import PublishMessage
from xss_receiver.utils import create_async_udp_socket

dns_cache = pylru.lrucache(constants.DNS_LRU_CACHE)


def parse_dns_query(qname: str) -> typing.List[typing.Tuple[str, int, int]]:
    query_result: typing.List[typing.Tuple[str, int, int]] = []

    ipv4_regexp = re.compile(r'[0-9]{1,3}(_[0-9]{1,3}){3}')
    ipv6_regexp = re.compile(r'[0-9a-f]{1,4}(_[0-9a-f]{1,4}){7}')

    qnames = qname.split('.')
    part_idx = 0
    found = False

    while part_idx < len(qnames):
        part = qnames[part_idx]
        qtype = None

        if ipv4_regexp.fullmatch(part) and all([0 <= int(i) <= 255 for i in part.split('_')]):
            qtype = dnslib.QTYPE.A
        elif ipv6_regexp.fullmatch(part):
            qtype = dnslib.QTYPE.AAAA
        elif found:  # 只解析连续的, 在已经找到一个合法的 part 的情况下, 遇到无法解析的就退出
            break

        if qtype:
            found = True

            count = 1
            if part_idx + 1 < len(qnames) and qnames[part_idx + 1].isdigit():
                part_idx += 1
                count = int(qnames[part_idx])

            if qtype == dnslib.QTYPE.A:
                part = part.replace('_', '.')
            elif qtype == dnslib.QTYPE.AAAA:
                part = part.replace('_', ':')
            query_result.append((part, count, qtype))
        part_idx += 1

    return query_result


class DNSQuery:
    qname: str
    parts: typing.List[typing.Tuple[str, int, int]]
    parts_sum: int
    curr_idx: int

    def __init__(self, qname):
        self.qname = qname
        self.parts = parse_dns_query(qname)
        self.parts_sum = sum([i[1] for i in self.parts])
        self.curr_idx = 0

    def next_response(self) -> dnslib.RR:
        response = None
        tmp_idx = self.curr_idx

        part = None
        for part in self.parts:
            tmp_idx -= part[1]
            if tmp_idx < 0:
                break

        if part[2] == dnslib.QTYPE.A:
            response = dnslib.RR(self.qname, part[2], rdata=dnslib.A(part[0]))
        elif part[2] == dnslib.QTYPE.AAAA:
            response = dnslib.RR(self.qname, part[2], rdata=dnslib.AAAA(part[0]))

        self.curr_idx += 1
        self.curr_idx %= self.parts_sum
        return response


async def process_packet(sck: socket.socket, packet_bytes: bytes, remote_addr: typing.Tuple[str, int]):
    session = session_maker()
    session: AsyncSession

    try:
        packet = dnslib.DNSRecord.parse(packet_bytes)
        if packet.header.opcode == 0:  # type == Query
            qname = packet.q.qname.idna()

            if system_config.DNS_KEY in qname:
                cache_key = qname + '@' + remote_addr[0]

                if cache_key in dns_cache:
                    query = dns_cache[cache_key]
                else:
                    query = DNSQuery(qname)
                    dns_cache[cache_key] = query

                if query.parts_sum != 0:
                    reply = packet.reply()
                    reply.add_answer(query.next_response())
                    sck.sendto(reply.pack(), remote_addr)

            dns_log = DNSLog(client_ip=remote_addr[0], transaction_id=packet.header.id, domain=qname, dns_type=packet.q.qtype, dns_class=packet.q.qclass)
            session.add(dns_log)
            await session.commit()

            publish_subscribe.publish(PublishMessage(msg_type=constants.PUBLISH_MESSAGE_TYPE_NEW_DNS_LOG, msg_content=packet.q.qname.idna()))
    except Exception as e:
        pass

    await session.close()


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
        asyncio.create_task(process_packet(sck, data, remote_addr))


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
