from secrets import compare_digest

from flask import Blueprint, request, jsonify
from xss_receiver.Config import LOGIN_SALT

from xss_receiver import cached_config, db
from xss_receiver.JWTAuth import jwt_auth, sign_token
from xss_receiver.Models import SystemLog
from xss_receiver.Response import Response
from xss_receiver.Utils import passwd_hash

auth_controller = Blueprint('auth_controller', __name__, static_folder=None, template_folder=None)


@auth_controller.route("/login", methods=['POST'])
def login():
    if isinstance(request.json, dict):
        password = request.json.get('password', None)
        username = request.json.get('username', None)

        if isinstance(username, str) and isinstance(password, str) and compare_digest(cached_config.ADMIN_PASSWORD, passwd_hash(password, LOGIN_SALT)):
            token = sign_token()
            system_log = SystemLog(log_content=f'Admin login with username [{username}]')
            db.session.add(system_log)
            db.session.commit()
            return jsonify(Response.success('登录成功', token))
        else:
            return jsonify(Response.failed('用户名或密码错误'))
    else:
        return jsonify(Response.invalid('无效请求'))


@auth_controller.route("/status", methods=['GET'])
def status():
    if jwt_auth:
        return jsonify(Response.success())
    else:
        return jsonify(Response.failed())


@auth_controller.route('/get_salt', methods=['GET'])
def get_salt():
    return jsonify(Response.success("", LOGIN_SALT))


'''
@auth_controller.route('/renew', methods=['POST'])
@auth_required
def renew():
    if isinstance(request.json, dict):
        is_renew = request.json.get('renew', None)
        if isinstance(is_renew, bool) and is_renew:
            return jsonify(Response.success('', sign_token().decode()))
        else:
            return jsonify(Response.failed('参数无效'))
    else:
        return jsonify(Response.invalid('参数无效'))
'''
