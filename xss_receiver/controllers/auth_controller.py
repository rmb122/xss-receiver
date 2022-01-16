import typing
from secrets import compare_digest

import sanic
from sanic import Blueprint, json
from sqlalchemy.future import select

from xss_receiver import system_config, constants, ip2region
from xss_receiver.jwt_auth import sign_token, auth_required, admin_required
from xss_receiver.models import User
from xss_receiver.response import Response
from xss_receiver.utils import passwd_hash, get_region_from_ip, add_system_log

auth_controller = Blueprint('auth_controller', __name__)


# database: pbkdf2_hmac(pbkdf2_hmac(password, username), PASSWORD_SALT))
# login: pbkdf2_hmac(password, username)
# verify: pbkdf2_hmac(login, PASSWORD_SALT) == database


@auth_controller.route("/login", methods=['POST'])
async def login(request: sanic.Request):
    if isinstance(request.json, dict):
        username = request.json.get('username', None)
        password = request.json.get('password', None)

        user: typing.Union[None, User] = (
            await request.ctx.db_session.execute(select(User).where(User.username == username))).scalar()

        if isinstance(username, str) and isinstance(password, str) and \
                (user is not None) and compare_digest(passwd_hash(password, system_config.PASSWORD_SALT), user.password):
            token = sign_token(user.user_id)

            log_content = f'Login with username [{username}] in [{request.ip} | {get_region_from_ip(request.ip, ip2region)}]'
            await add_system_log(request.ctx.db_session, log_content, constants.LOG_TYPE_LOGIN)

            return json(Response.success('登录成功', {'token': token, 'user_type': user.user_type}))
        else:
            return json(Response.failed('用户名或密码错误'))
    else:
        return json(Response.invalid('无效请求'))


@auth_controller.route("/register", methods=['POST'])
@admin_required
async def register(request: sanic.Request):
    username = request.json.get('username', None)
    password = request.json.get('password', None)

    user = (await request.ctx.db_session.execute(select(User).where(User.username == username))).scalar()
    if user is None:
        if isinstance(username, str) and isinstance(password, str) and len(username) < 255:
            user = User(username=username, password=passwd_hash(password, system_config.PASSWORD_SALT), user_type=constants.USER_TYPE_NORMAL)
            request.ctx.db_session.add(user)
            await request.ctx.db_session.commit()
            return json(Response.success('注册成功'))
        else:
            return json(Response.invalid('无效请求'))
    else:
        return json(Response.failed('用户名已经被注册'))


@auth_controller.route("/list_user", methods=['GET'])
@admin_required
async def list_user(request: sanic.Request):
    users = (await request.ctx.db_session.execute(select(User.username, User.user_type))).fetchall()
    users = [{'username': user, 'user_type': user_type} for user, user_type in users]
    return json(Response.success('', users))


@auth_controller.route("/delete", methods=['POST'])
@admin_required
async def delete(request: sanic.Request):
    username = request.json.get('username', None)

    if isinstance(username, str):
        user = (await request.ctx.db_session.execute(select(User).where(User.username == username))).scalar()
        # 只能删除普通用户
        if user is not None and user.user_type == constants.USER_TYPE_NORMAL:
            await request.ctx.db_session.delete(user)
            await request.ctx.db_session.commit()
            return json(Response.success('删除成功'))
        else:
            return json(Response.failed('用户不存在'))
    else:
        return json(Response.invalid('无效请求'))


@auth_controller.route("/change_password", methods=['POST'])
@auth_required
async def change_password(request: sanic.Request):
    target_user = request.json.get('target_user', None)
    original_password = request.json.get('original_password', None)
    new_password = request.json.get('new_password', None)

    if target_user is None and isinstance(original_password, str) and isinstance(new_password, str) \
            and compare_digest(request.ctx.user.password, passwd_hash(original_password, system_config.PASSWORD_SALT)):

        request.ctx.user.password = passwd_hash(new_password, system_config.PASSWORD_SALT)
        request.ctx.db_session.add(request.ctx.user)

        await request.ctx.db_session.commit()
        return json(Response.success('修改成功'))
    elif target_user is not None and request.ctx.user.user_type == constants.USER_TYPE_SUPER_ADMIN \
            and isinstance(new_password, str) and isinstance(target_user, str):
        # 超级用户修改普通用户不需要原密码
        user = (await request.ctx.db_session.execute(select(User).where(User.username == target_user))).scalar()
        if user is not None and user.user_type == constants.USER_TYPE_NORMAL:
            user.password = passwd_hash(new_password, system_config.PASSWORD_SALT)
            request.ctx.db_session.add(request.ctx.user)

            await request.ctx.db_session.commit()
            return json(Response.success('修改成功'))
        else:
            return json(Response.failed('用户不存在'))
    else:
        return json(Response.invalid('无效请求'))


@auth_controller.route("/status", methods=['GET'])
async def status(request: sanic.Request):
    if request.ctx.auth:
        return json(Response.success('', request.ctx.user.user_type))
    else:
        return json(Response.failed())
