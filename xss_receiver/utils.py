import random
from functools import wraps
import aiofiles
import hashlib

import sanic


def random_string(len):
    return "".join(random.choices("0123456789abcdef", k=len))


def passwd_hash(password: str, salt: str):
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 23333).hex()


def format_region(region):
    try:
        region = region['region'].decode()
        region = region.split('|')
        tmp = []
        for k in region:
            if k != '0':
                tmp.append(k)
            if k == '内网IP':
                return '局域网'
        return ''.join(tmp)
    except Exception:
        return '解析错误'


def get_region_from_ip(ip, ip2Region):
    '''
    TODO: add ipv6 support
    :param ip:
    :param ip2Region:
    :return:
    '''
    if ":" not in ip:
        region = ""
        retry = 0
        while not region and retry < 3:
            try:
                region = ip2Region.btreeSearch(ip)
            except Exception:
                retry += 1
                pass
        if region == "":
            return "转换中出错"
        return format_region(region)
    else:
        return "不支持 IPv6 查询"


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


async def write_file(path, body):
    async with aiofiles.open(path, 'wb') as f:
        await f.write(body)


async def read_file(path):
    async with aiofiles.open(path, 'rb') as f:
        return await f.read()
