from functools import wraps
from time import time

import jwt
from flask import request, jsonify, _request_ctx_stack, make_response
from werkzeug.local import LocalProxy

from xss_receiver.Constants import JWT_HEADER
from xss_receiver.Config import SECRET_KEY
from xss_receiver.Response import Response

jwt_auth = LocalProxy(lambda: getattr(_request_ctx_stack.top, 'jwt_auth', None))


def sign_token(expire_time=259200):
    return jwt.encode({'login_status': True, 'expire': time() + expire_time}, SECRET_KEY, algorithm='HS256')


def verify_token(token):
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        if decoded['expire'] > time():
            return decoded['login_status']
        else:
            return False
    except Exception as e:
        return False


def auth_required(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        if JWT_HEADER in request.headers and verify_token(request.headers[JWT_HEADER]):
            return func(*args, **kwargs)
        else:
            return make_response(jsonify(Response(403, 'Forbidden')), 403)

    return decorator


def init_app(app):
    @app.before_request
    def get_jwt_auth():
        if JWT_HEADER in request.headers and verify_token(request.headers[JWT_HEADER]):
            _request_ctx_stack.top.jwt_auth = True
        else:
            _request_ctx_stack.top.jwt_auth = False
