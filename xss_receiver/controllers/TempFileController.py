from os import listdir, unlink
from os.path import join, exists, getsize

from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from xss_receiver.Config import TEMP_FILE_PATH

from xss_receiver.Constants import MAX_PREVIEW_SIZE
from xss_receiver.JWTAuth import auth_required
from xss_receiver.Response import Response

temp_file_controller = Blueprint('temp_file_controller', __name__, static_folder=None, template_folder=None)


@temp_file_controller.route('/delete_all', methods=['POST'])
@auth_required
def delete_all():
    if isinstance(request.json, dict):
        delete = request.json.get('delete', None)
        if isinstance(delete, bool) and delete:
            temp_files = listdir(TEMP_FILE_PATH)
            for filename in temp_files:
                path = join(TEMP_FILE_PATH, filename)
                unlink(path)
            return jsonify(Response.success("清空成功"))
        else:
            return jsonify(Response.invalid('无效请求'))
    else:
        return jsonify(Response.invalid('无效请求'))


@temp_file_controller.route('/download', methods=['POST'])
@auth_required
def download():
    if isinstance(request.json, dict):
        filename = request.json.get('filename', None)
        if isinstance(filename, str):
            filename = secure_filename(filename)
            path = join(TEMP_FILE_PATH, filename)
            if exists(path):
                return send_file(path, as_attachment=True, attachment_filename=filename)
            else:
                return jsonify(Response.failed('文件不存在')), 400
        else:
            return jsonify(Response.invalid('参数无效')), 400
    else:
        return jsonify(Response.invalid('参数无效')), 400


@temp_file_controller.route('/preview', methods=['POST'])
@auth_required
def preview():
    if isinstance(request.json, dict):
        filename = request.json.get('filename', None)
        if isinstance(filename, str):
            filename = secure_filename(filename)
            path = join(TEMP_FILE_PATH, filename)
            if exists(path) and getsize(path) < MAX_PREVIEW_SIZE:
                file = open(path, 'rb')
                content = file.read()
                try:
                    content = content.decode('utf-8')
                    return jsonify(Response.success('', content))
                except Exception:
                    return jsonify(Response.failed('文件过大或者文件不是纯文本, 无法预览'))
            else:
                return jsonify(Response.failed('文件不存在'))
        else:
            return jsonify(Response.invalid('参数无效'))
    else:
        return jsonify(Response.invalid('参数无效'))
