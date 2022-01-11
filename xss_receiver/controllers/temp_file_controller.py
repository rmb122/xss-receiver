from os import listdir, unlink
from os.path import join, exists, getsize

from sanic import Blueprint, json
import sanic
from xss_receiver.utils import read_file
from werkzeug.utils import secure_filename
from xss_receiver import system_config

from xss_receiver.jwt_auth import auth_required
from xss_receiver.response import Response

temp_file_controller = Blueprint('temp_file_controller', __name__)


@temp_file_controller.route('/delete_all', methods=['POST'])
@auth_required
async def delete_all(request: sanic.Request):
    if isinstance(request.json, dict):
        delete = request.json.get('delete', None)

        if isinstance(delete, bool) and delete:
            temp_files = listdir(system_config.TEMP_FILE_PATH)
            for filename in temp_files:
                path = join(system_config.TEMP_FILE_PATH, filename)
                unlink(path)
            return json(Response.success("清空成功"))
        else:
            return json(Response.invalid('无效请求'))
    else:
        return json(Response.invalid('无效请求'))


@temp_file_controller.route('/download', methods=['POST'])
@auth_required
async def download(request: sanic.Request):
    if isinstance(request.json, dict):
        filename = request.json.get('filename', None)
        if isinstance(filename, str):
            filename = secure_filename(filename)
            path = join(system_config.TEMP_FILE_PATH, filename)
            if exists(path):
                return await sanic.response.file(path, filename=filename)
            else:
                return json(Response.failed('文件不存在'), 500)
        else:
            return json(Response.invalid('参数无效'), 400)
    else:
        return json(Response.invalid('参数无效'), 400)


@temp_file_controller.route('/preview', methods=['POST'])
@auth_required
async def preview(request: sanic.Request):
    if isinstance(request.json, dict):
        filename = request.json.get('filename', None)
        if isinstance(filename, str):
            filename = secure_filename(filename)
            path = join(system_config.TEMP_FILE_PATH, filename)
            if exists(path):
                if getsize(path) < system_config.MAX_PREVIEW_SIZE:
                    content = await read_file(path)
                    try:
                        content = content.decode('utf-8')
                        return json(Response.success('', content))
                    except Exception:
                        return json(Response.failed('文件不是纯文本, 无法预览'))
                else:
                    json(Response.failed('文件过大, 无法预览'))
            else:
                return json(Response.failed('文件不存在'))
        else:
            return json(Response.invalid('参数无效'))
    else:
        return json(Response.invalid('参数无效'))
