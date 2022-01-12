from functools import wraps
from time import time

import jwt
import sanic
from sqlalchemy.future import select

from xss_receiver import system_config, constants
from xss_receiver.models import User
from xss_receiver.response import Response


def sign_token(user_id, expire_time=259200):
    return jwt.encode({
        'login_status': True,
        'expire': time() + expire_time,
        'user_id': user_id
    }, system_config.SECRET_KEY, algorithm='HS256')


def verify_token(token):
    try:
        decoded = jwt.decode(token, system_config.SECRET_KEY, algorithms=['HS256'])
        if decoded['expire'] > time():
            return decoded['login_status'], decoded['user_id']
        else:
            return False, -1
    except Exception as e:
        return False, -1


def auth_required(func):
    @wraps(func)
    async def decorator(request: sanic.Request, *args, **kwargs):
        if request.ctx.auth:
            return await func(request, *args, **kwargs)
        else:
            return sanic.response.json(Response().failed('Login required'), 403)

    return decorator


def admin_required(func):
    @wraps(func)
    async def decorator(request: sanic.Request, *args, **kwargs):
        if request.ctx.auth and request.ctx.user.user_type == constants.USER_TYPE_SUPER_ADMIN:
            return await func(request, *args, **kwargs)
        else:
            return sanic.response.json(Response().failed('Super admin required'), 403)

    return decorator


def install_jwt_auth_middleware(app: sanic.Sanic):
    @app.middleware("request")
    async def jwt_auth_middleware(request):
        request.ctx.auth = False
        request.ctx.user = None

        if constants.JWT_HEADER in request.headers:
            login_status, user_id = verify_token(request.headers[constants.JWT_HEADER])
            if login_status:
                user = (await request.ctx.db_session.execute(select(User).where(User.user_id == user_id))).scalar()
                if user is not None:
                    request.ctx.auth = True
                    request.ctx.user = user
