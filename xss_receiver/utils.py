import asyncio
import hashlib
import os
import os.path
import random
import typing
from functools import wraps

import aiofiles
import asyncudp
import sanic
from werkzeug.utils import secure_filename

from xss_receiver import models
from xss_receiver.asserts.ip2region import Ip2Region
from xss_receiver.asserts.ipdbv6 import IPDBv6


def random_string(len):
    return "".join(random.choices("0123456789abcdef", k=len))


def passwd_hash(password: str, salt: str):
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 23333).hex()


def format_region(region):
    region = region['region'].decode()
    region = region.split('|')
    tmp = []
    for k in region:
        if k != '0':
            tmp.append(k)
        if k == '内网IP':
            return '局域网'
    return ''.join(tmp)


_ipv4db = Ip2Region(f'{os.path.dirname(__file__)}/asserts/ip2region.db')
_ipv6db = IPDBv6(f'{os.path.dirname(__file__)}/asserts/ipv6wry.db')


def get_region_from_ip(ip):
    ip = ip.strip('[]')
    if ip.startswith('::ffff:'):
        ip = ip[7:]

    try:
        if ":" not in ip:
            region = _ipv4db.btreeSearch(ip)
            return format_region(region)
        else:
            return _ipv6db.getIPAddr(ip, None)[2].replace('\t', '').replace(' ', '')
    except Exception:
        return '查询中出错'


def process_headers(func):
    @wraps(func)
    async def _process_headers(request: sanic.Request, *args, **kwargs):
        if request.method == 'OPTIONS':
            response = sanic.response.text('', 200)
        else:
            response = await func(request, *args, **kwargs)

        response.headers['Server'] = 'nginx'

        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
        response.headers['Access-Control-Allow-Headers'] = '*'
        return response

    return _process_headers


async def write_file(path, body, mode='wb'):
    async with aiofiles.open(path, mode) as f:
        await f.write(body)


async def read_file(path, mode='rb'):
    async with aiofiles.open(path, mode) as f:
        return await f.read()


def filter_list(input_dict: typing.Dict):
    output_dict = {}
    for key, value in input_dict.items():
        if isinstance(value, list) and len(value) == 1:
            output_dict[key] = value[0]
    return output_dict


def fix_upper_case(header_dict: typing.Dict):
    output_dict = {}
    for key, value in header_dict.items():
        key = key.split('-')
        key = '-'.join([i.capitalize() for i in key])
        output_dict[key] = value
    return output_dict


def secure_filename_with_directory(filename: str):
    parts = filename.split(os.sep)
    full_path = os.path.join(*[secure_filename(i) for i in parts])
    return full_path.strip(os.sep)  # 应该是不需要的, 以防万一


async def add_system_log(db_session, content, log_type):
    system_log = models.SystemLog(log_content=content, log_type=log_type)
    db_session.add(system_log)
    await db_session.commit()


async def create_async_udp_socket(local_addr=None, remote_addr=None, sock=None):
    """Create a UDP socket with given local and remote addresses.

    >>> sock = await asyncudp.create_socket(local_addr=('127.0.0.1', 9999))

    """

    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        asyncudp._SocketProtocol,
        local_addr=local_addr,
        remote_addr=remote_addr,
        sock=sock
    )

    return asyncudp.Socket(transport, protocol)
