from functools import wraps
from time import time

import jwt
import sanic

from xss_receiver.constants import JWT_HEADER
from xss_receiver import system_config
from xss_receiver.response import Response


def sign_token(expire_time=259200):
    return jwt.encode({'login_status': True, 'expire': time() + expire_time}, system_config.SECRET_KEY, algorithm='HS256')


def verify_token(token):
    try:
        decoded = jwt.decode(token, system_config.SECRET_KEY, algorithms=['HS256'])
        if decoded['expire'] > time():
            return decoded['login_status']
        else:
            return False
    except Exception as e:
        return False


def auth_required(func):
    @wraps(func)
    async def decorator(request: sanic.Request, *args, **kwargs):
        if JWT_HEADER in request.headers and verify_token(request.headers[JWT_HEADER]):
            return func(request, *args, **kwargs)
        else:
            return sanic.response.json(Response().failed('Forbidden'), 403)

    return decorator
