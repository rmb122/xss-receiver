import hashlib
import os.path
import random
import json
import typing
from functools import wraps

import aiofiles
import jinja2.sandbox
import sanic
from werkzeug.utils import secure_filename
from xss_receiver import models


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


async def render_dynamic_template(template: str, _globals: typing.Dict[str, typing.Any]):
    env = jinja2.sandbox.SandboxedEnvironment(extensions=['jinja2.ext.do'], enable_async=True)
    result = ""
    error = None

    try:
        result = await env.from_string(template).render_async(_globals)
    except Exception as e:
        error = e

    return result, error


def generate_dynamic_template_globals(system_config, response: sanic.HTTPResponse, client_ip, path, method, header, arg, body):
    _globals = {}

    def add_header(name, value):
        if isinstance(name, str) and isinstance(value, str):
            response.headers.add(name, value)

    def pop_header(name):
        if isinstance(name, str):
            response.headers.pop(name)

    def set_status(code):
        if isinstance(code, int):
            response.status = code

    async def get_upload_file(filename):
        if isinstance(filename, str):
            filename = secure_filename(filename)
            return await read_file(os.path.join(system_config.UPLOAD_PATH, filename))
        else:
            return None

    _globals['add_header'] = add_header
    _globals['pop_header'] = pop_header
    _globals['set_status'] = set_status
    _globals['get_upload_file'] = get_upload_file
    _globals['json_encode'] = json.dumps
    _globals['json_decode'] = json.loads

    _globals['client_ip'] = client_ip
    _globals['path'] = path
    _globals['method'] = method
    _globals['header'] = header
    _globals['arg'] = arg
    _globals['body'] = body

    return _globals


async def add_system_log(db_session, content, log_type):
    system_log = models.SystemLog(log_content=content, log_type=log_type)
    db_session.add(system_log)
    await db_session.commit()
