import hashlib
import json
import os
import os.path
import random
import shutil
import typing
import urllib.parse
from functools import wraps

import aiofiles
import jinja2.sandbox
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


async def render_dynamic_template(template: str, _globals: typing.Dict[str, typing.Any]):
    env = jinja2.sandbox.SandboxedEnvironment(extensions=['jinja2.ext.do'], enable_async=True)
    result = ""
    error = None

    try:
        result = await env.from_string(template).render_async(_globals)
    except Exception as e:
        error = e

    return result, error


def secure_filename_with_directory(filename: str):
    parts = filename.split(os.sep)
    full_path = os.path.join(*[secure_filename(i) for i in parts])
    return full_path.strip(os.sep)  # 应该是不需要的, 以防万一


def generate_dynamic_template_globals(system_config, request: sanic.Request, response: sanic.HTTPResponse, client_ip, path, method, header, arg, body, file, extra_output):
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

    def write_output(output):
        if isinstance(output, bytes):
            extra_output.append(output)
        elif isinstance(output, str):
            extra_output.append(output.encode())
        elif isinstance(output, list):
            extra_output.append(bytes(output))

    def list_directory(directory_name):
        if isinstance(directory_name, str):
            directory_name = secure_filename(directory_name)
            entries = os.scandir(os.path.join(system_config.UPLOAD_PATH, directory_name))
            return [(i.name, i.is_dir()) for i in entries]

    def create_directory(directory_name):
        if isinstance(directory_name, str):
            directory_name = secure_filename(directory_name)
            if len(directory_name) > 0:
                os.mkdir(os.path.join(system_config.UPLOAD_PATH, directory_name))

    def delete_directory(directory_name):
        if isinstance(directory_name, str):
            directory_name = secure_filename(directory_name)
            if len(directory_name) > 0:
                shutil.rmtree(os.path.join(system_config.UPLOAD_PATH, directory_name))

    def delete_upload_file(filename):
        if isinstance(filename, str):
            filename = secure_filename_with_directory(filename)
            os.unlink(filename)

    async def read_upload_file(filename, binary=False):
        if isinstance(filename, str) and isinstance(binary, bool):
            filename = secure_filename_with_directory(filename)

            if binary:
                read_mode = 'rb'
            else:
                read_mode = 'r'

            return await read_file(os.path.join(system_config.UPLOAD_PATH, filename), read_mode)

    async def write_upload_file(filename, content, append=False):
        if isinstance(filename, str) and isinstance(append, bool) and (isinstance(content, str) or isinstance(content, bytes)):
            filename = secure_filename_with_directory(filename)

            if append:
                write_mode = 'a'
            else:
                write_mode = 'w'

            if isinstance(content, bytes):
                write_mode += 'b'

            return await write_file(os.path.join(system_config.UPLOAD_PATH, filename), content, write_mode)

    def get_request_upload_file(file_key):
        if isinstance(file_key, str) and file_key in request.files:
            f = request.files.get(file_key)
            return f.name, f.body

    def catch_exception(func):
        def new_func(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception:
                return None

        return new_func

    _globals['add_header'] = catch_exception(add_header)
    _globals['pop_header'] = catch_exception(pop_header)
    _globals['set_status'] = catch_exception(set_status)
    _globals['write_output'] = catch_exception(write_output)

    _globals['list_directory'] = catch_exception(list_directory)
    _globals['create_directory'] = catch_exception(create_directory)
    _globals['delete_directory'] = catch_exception(delete_directory)
    _globals['delete_upload_file'] = catch_exception(delete_upload_file)
    _globals['read_upload_file'] = catch_exception(read_upload_file)
    _globals['write_upload_file'] = catch_exception(write_upload_file)
    _globals['get_request_upload_file'] = catch_exception(get_request_upload_file)

    _globals['json_encode'] = catch_exception(json.dumps)
    _globals['json_decode'] = catch_exception(json.loads)
    _globals['url_encode'] = catch_exception(urllib.parse.quote)
    _globals['url_decode'] = catch_exception(urllib.parse.unquote)
    _globals['url_parse_qs'] = catch_exception(urllib.parse.parse_qs)

    _globals['client_ip'] = client_ip
    _globals['path'] = path
    _globals['method'] = method
    _globals['header'] = header
    _globals['arg'] = arg
    _globals['body'] = body
    _globals['file'] = file

    return _globals


async def add_system_log(db_session, content, log_type):
    system_log = models.SystemLog(log_content=content, log_type=log_type)
    db_session.add(system_log)
    await db_session.commit()
