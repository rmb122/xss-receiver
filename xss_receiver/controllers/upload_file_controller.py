import asyncio
from os import scandir, unlink, rename, mkdir
from os.path import join, exists, getsize, getmtime, isdir, isfile
import shutil

import sanic
from sanic import Blueprint, json
from werkzeug.utils import secure_filename

from xss_receiver import system_config
from xss_receiver.jwt_auth import auth_required
from xss_receiver.response import Response
from xss_receiver.utils import write_file, read_file, secure_filename_with_directory

upload_file_controller = Blueprint('upload_file_controller', __name__)


@upload_file_controller.route('/add', methods=['POST'])
@auth_required
async def add(request: sanic.Request):
    file = request.files.get('file', None)
    if file:
        filename = secure_filename_with_directory(file.name)
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
    def get_dir_files(path: str, base=''):
        files = []
        for entry in scandir(path):
            files.append({
                'filename': entry.name,
                'path': join(base, entry.name),
                'size': entry.stat().st_size,
                'mttime': entry.stat().st_mtime,
                'dir': entry.is_dir()
            })
        files = sorted(files, key=lambda x: x['filename'])
        return files

    files = get_dir_files(system_config.UPLOAD_PATH)
    for file in files:  # 只支持一层深度
        if file['dir']:
            file['children'] = get_dir_files(join(system_config.UPLOAD_PATH, file['filename']), file['filename'])
    return json(Response.success('', files))


@upload_file_controller.route('/delete', methods=['POST'])
@auth_required
async def delete(request: sanic.Request):
    if isinstance(request.json, dict):
        filename = request.json.get('filename', None)
        if isinstance(filename, str):
            filename = secure_filename_with_directory(filename)
            path = join(system_config.UPLOAD_PATH, filename)
            if exists(path) and not isdir(path):
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
            filename = secure_filename_with_directory(filename)
            path = join(system_config.UPLOAD_PATH, filename)
            if exists(path) and not isdir(path):
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
            filename = secure_filename_with_directory(filename)
            path = join(system_config.UPLOAD_PATH, filename)
            if exists(path) and not isdir(path):
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
                return json(Response.failed('文件不存在或者为文件夹'))
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
            filename = secure_filename_with_directory(filename)
            path = join(system_config.UPLOAD_PATH, filename)
            if exists(path) and not isdir(path):
                if isinstance(content, str):
                    await write_file(path, content.encode())

                if isinstance(new_filename, str):
                    new_filename = secure_filename_with_directory(new_filename)
                    new_path = join(system_config.UPLOAD_PATH, new_filename)
                    if not exists(new_path):
                        try:
                            rename(path, new_path)
                            return json(Response.success('修改成功'))
                        except FileNotFoundError:
                            return json(Response.failed('重命名失败, 请确认新文件所在文件夹存在'))
                    else:
                        return json(Response.failed('重命名失败, 目标文件名已存在'))
            else:
                return json(Response.failed('文件不存在'))
        else:
            return json(Response.invalid('参数无效'))
    else:
        return json(Response.invalid('参数无效'))


@upload_file_controller.route('/add_directory', methods=['POST'])
@auth_required
async def add_directory(request: sanic.Request):
    if isinstance(request.json, dict):
        directory_name = request.json.get('directory_name', None)
        if isinstance(directory_name, str) and len(secure_filename(directory_name)) > 0:
            directory_name = secure_filename(directory_name)
            full_path = join(system_config.UPLOAD_PATH, directory_name)
            if not exists(full_path):
                mkdir(full_path)
                return json(Response.success('创建成功'))
            else:
                return json(Response.failed('文件夹已存在'))
        else:
            return json(Response.invalid('参数无效'))
    else:
        return json(Response.invalid('参数无效'))


@upload_file_controller.route('/delete_directory', methods=['POST'])
@auth_required
async def delete_directory(request: sanic.Request):
    if isinstance(request.json, dict):
        directory_name = request.json.get('directory_name', None)
        if isinstance(directory_name, str) and len(secure_filename(directory_name)) > 0:
            directory_name = secure_filename(directory_name)
            full_path = join(system_config.UPLOAD_PATH, directory_name)
            if exists(full_path) and not isfile(full_path):
                shutil.rmtree(full_path)
                return json(Response.success('删除成功'))
            else:
                return json(Response.failed('文件夹不存在'))
        else:
            return json(Response.invalid('参数无效'))
    else:
        return json(Response.invalid('参数无效'))


@upload_file_controller.route('modify_directory', methods=['POST'])
@auth_required
async def modify_directory(request: sanic.Request):
    if isinstance(request.json, dict):
        directory_name = request.json.get('directory_name', None)
        new_directory_name = request.json.get('new_directory_name', None)

        if isinstance(directory_name, str) and len(secure_filename(directory_name)) > 0 and len(secure_filename(new_directory_name)) > 0:
            full_path = join(system_config.UPLOAD_PATH, secure_filename(directory_name))
            new_full_path = join(system_config.UPLOAD_PATH, secure_filename(new_directory_name))

            if exists(full_path) and not exists(new_full_path):
                rename(full_path, new_full_path)
                return json(Response.success('重命名成功'))
            else:
                return json(Response.failed('目标文件夹名已存在'))
        else:
            return json(Response.invalid('参数无效'))
    else:
        return json(Response.invalid('参数无效'))
