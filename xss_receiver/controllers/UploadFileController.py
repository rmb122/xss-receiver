from os import listdir, unlink, rename
from os.path import join, exists, getsize, getmtime, isdir

from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from xss_receiver.config import UPLOAD_PATH

from xss_receiver.constants import MAX_PREVIEW_SIZE
from xss_receiver.jwt_auth import auth_required
from xss_receiver.response import Response

upload_file_controller = Blueprint('upload_file_controller', __name__, static_folder=None, template_folder=None)


@upload_file_controller.route('/add', methods=['POST'])
@auth_required
def add():
    file = request.files.get('file', None)
    if file:
        filename = secure_filename(file.filename)
        path = join(UPLOAD_PATH, filename)
        if not exists(path):
            file.save(path)
            return jsonify(Response.success('上传成功'))
        else:
            return jsonify(Response.failed('已存在同名文件'))
    else:
        return jsonify(Response.invalid('无效参数'))


@upload_file_controller.route('/list', methods=['GET'])
@auth_required
def list():
    file_list = listdir(UPLOAD_PATH)
    payload = []

    for file in file_list:
        path = join(UPLOAD_PATH, file)
        size = getsize(path)
        mttime = getmtime(path)
        _isdir = isdir(path)
        payload.append({'filename': file, 'size': size, 'mttime': mttime, 'dir': _isdir})
    return jsonify(Response.success('', payload))


@upload_file_controller.route('/delete', methods=['POST'])
@auth_required
def delete():
    if isinstance(request.json, dict):
        filename = request.json.get('filename', None)
        if isinstance(filename, str):
            filename = secure_filename(filename)
            path = join(UPLOAD_PATH, filename)
            if exists(path):
                unlink(path)
                return jsonify(Response.success('删除成功'))
            else:
                return jsonify(Response.failed('删除的文件不存在'))
        else:
            return jsonify(Response.invalid('参数无效'))
    else:
        return jsonify(Response.invalid('参数无效'))


@upload_file_controller.route('/download', methods=['POST'])
@auth_required
def download():
    if isinstance(request.json, dict):
        filename = request.json.get('filename', None)
        if isinstance(filename, str):
            filename = secure_filename(filename)
            path = join(UPLOAD_PATH, filename)
            if exists(path):
                return send_file(path, as_attachment=True, attachment_filename=filename)
            else:
                return jsonify(Response.failed('文件不存在')), 400
        else:
            return jsonify(Response.invalid('参数无效')), 400
    else:
        return jsonify(Response.invalid('参数无效')), 400


@upload_file_controller.route('/preview', methods=['POST'])
@auth_required
def preview():
    if isinstance(request.json, dict):
        filename = request.json.get('filename', None)
        if isinstance(filename, str):
            filename = secure_filename(filename)
            path = join(UPLOAD_PATH, filename)
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


@upload_file_controller.route('/modify', methods=['POST'])
@auth_required
def modify():
    if isinstance(request.json, dict):
        filename = request.json.get('filename', None)
        new_filename = request.json.get('new_filename', None)
        content = request.json.get('content', None)
        if isinstance(filename, str):
            filename = secure_filename(filename)
            path = join(UPLOAD_PATH, filename)
            if exists(path):
                if isinstance(content, str):
                    file = open(path, 'w')
                    file.write(content)
                    file.close()

                if isinstance(new_filename, str):
                    new_filename = secure_filename(new_filename)
                    rename(path, join(UPLOAD_PATH, new_filename))

                return jsonify(Response.success('修改成功'))
            else:
                return jsonify(Response.failed('文件不存在'))
        else:
            return jsonify(Response.invalid('参数无效'))
    else:
        return jsonify(Response.invalid('参数无效'))
