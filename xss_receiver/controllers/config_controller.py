from secrets import compare_digest

from flask import Blueprint, request, jsonify
from xss_receiver.config import LOGIN_SALT

from xss_receiver import cached_config
from xss_receiver.jwt_auth import auth_required
from xss_receiver.response import Response
from xss_receiver.utils import passwd_hash

config_controller = Blueprint('config_controller', __name__, static_folder=None, template_folder=None)


@config_controller.route('/modify', methods=['POST'])
@auth_required
def modify():
    if isinstance(request.json, dict):
        TEMP_FILE_SAVE = request.json.get('TEMP_FILE_SAVE', None)
        RECV_MAIL_ADDR = request.json.get('RECV_MAIL_ADDR', None)
        ADMIN_PASSWORD = request.json.get('ADMIN_PASSWORD', None)
        ORIGINAL_ADMIN_PASSWORD = request.json.get('ORIGINAL_ADMIN_PASSWORD', None)

        if isinstance(TEMP_FILE_SAVE, bool):
            cached_config.TEMP_FILE_SAVE = TEMP_FILE_SAVE
        if isinstance(RECV_MAIL_ADDR, str):
            cached_config.RECV_MAIL_ADDR = RECV_MAIL_ADDR
        if isinstance(ADMIN_PASSWORD, str) and isinstance(ORIGINAL_ADMIN_PASSWORD, str):
            if compare_digest(cached_config.ADMIN_PASSWORD, passwd_hash(ORIGINAL_ADMIN_PASSWORD, LOGIN_SALT)):
                cached_config.ADMIN_PASSWORD = passwd_hash(ADMIN_PASSWORD, LOGIN_SALT)
                return jsonify(Response.success('修改成功'))
            else:
                return jsonify(Response.failed('原密码错误'))
        return jsonify(Response.success('修改成功'))
    else:
        return jsonify(Response.invalid('参数无效'))


@config_controller.route('/list', methods=['GET'])
@auth_required
def list():
    configs = {'TEMP_FILE_SAVE': cached_config.TEMP_FILE_SAVE, 'RECV_MAIL_ADDR': cached_config.RECV_MAIL_ADDR}
    return jsonify(Response.success("", configs))
