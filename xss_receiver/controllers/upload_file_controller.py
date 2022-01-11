import asyncio
from os import listdir, unlink, rename
from os.path import join, exists, getsize, getmtime, isdir

import sanic
from sanic import Blueprint, json
from werkzeug.utils import secure_filename

from xss_receiver import system_config
from xss_receiver.jwt_auth import auth_required
from xss_receiver.response import Response
from xss_receiver.utils import write_file, read_file

upload_file_controller = Blueprint('upload_file_controller', __name__)


@upload_file_controller.route('/add', methods=['POST'])
@auth_required
async def add(request: sanic.Request):
    file = request.files.get('file', None)
    if file:
        filename = secure_filename(file.name)
        path = join(system_config.UPLOAD_PATH, filename)
        if not exists(path):
            asyncio.create_task(write_file(path, file.body))
            return json(Response.success('上传成功'))
        else:
            return json(Response.failed('已存在同名文件'))
    else:
        return json(Response.invalid('无效参数'))


@upload_file_controller.route('/list', methods=['GET'])
@auth_required
async def file_list(request: sanic.Request):
    files = listdir(system_config.UPLOAD_PATH)
    payload = []

    for filename in files:
        path = join(system_config.UPLOAD_PATH, filename)
        payload.append({'filename': filename, 'size': getsize(path), 'mttime': getmtime(path), 'dir': isdir(path)})
    return json(Response.success('', payload))


@upload_file_controller.route('/delete', methods=['POST'])
@auth_required
async def delete(request: sanic.Request):
    if isinstance(request.json, dict):
        filename = request.json.get('filename', None)
        if isinstance(filename, str):
            filename = secure_filename(filename)
            path = join(system_config.UPLOAD_PATH, filename)
            if exists(path):
                unlink(path)
                return json(Response.success('删除成功'))
            else:
                return json(Response.failed('删除的文件不存在'))
        else:
            return json(Response.invalid('参数无效'))
    else:
        return json(Response.invalid('参数无效'))


@upload_file_controller.route('/download', methods=['POST'])
@auth_required
async def download(request: sanic.Request):
    if isinstance(request.json, dict):
        filename = request.json.get('filename', None)
        if isinstance(filename, str):
            filename = secure_filename(filename)
            path = join(system_config.UPLOAD_PATH, filename)
            if exists(path):
                return await sanic.response.file(path, filename=filename)
            else:
                return json(Response.failed('文件不存在'), 500)
        else:
            return json(Response.invalid('参数无效'), 400)
    else:
        return json(Response.invalid('参数无效'), 400)


@upload_file_controller.route('/preview', methods=['POST'])
@auth_required
async def preview(request: sanic.Request):
    if isinstance(request.json, dict):
        filename = request.json.get('filename', None)
        if isinstance(filename, str):
            filename = secure_filename(filename)
            path = join(system_config.UPLOAD_PATH, filename)
            if exists(path):
                if getsize(path) < system_config.MAX_PREVIEW_SIZE:
                    content = await read_file(path)
                    try:
                        content = content.decode('utf-8')
                        return json(Response.success('', content))
                    except Exception:
                        return json(Response.failed('文件不是纯文本, 无法预览'))
                else:
                    return json(Response.failed('文件过大, 无法预览'))
            else:
                return json(Response.failed('文件不存在'))
        else:
            return json(Response.invalid('参数无效'))
    else:
        return json(Response.invalid('参数无效'))


@upload_file_controller.route('/modify', methods=['POST'])
@auth_required
async def modify(request: sanic.Request):
    if isinstance(request.json, dict):
        filename = request.json.get('filename', None)
        new_filename = request.json.get('new_filename', None)
        content = request.json.get('content', None)

        if isinstance(filename, str):
            filename = secure_filename(filename)
            path = join(system_config.UPLOAD_PATH, filename)
            if exists(path):
                if isinstance(content, str):
                    await write_file(path, content.encode())

                if isinstance(new_filename, str):
                    new_filename = secure_filename(new_filename)
                    rename(path, join(system_config.UPLOAD_PATH, new_filename))

                return json(Response.success('修改成功'))
            else:
                return json(Response.failed('文件不存在'))
        else:
            return json(Response.invalid('参数无效'))
    else:
        return json(Response.invalid('参数无效'))
