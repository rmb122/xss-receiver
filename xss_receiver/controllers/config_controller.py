import sanic
from sanic import Blueprint, json

from xss_receiver import system_config
from xss_receiver.jwt_auth import auth_required
from xss_receiver.response import Response

config_controller = Blueprint('config_controller', __name__)


@config_controller.route('/modify', methods=['POST'])
@auth_required
async def modify(request: sanic.Request):
    if isinstance(request.json, dict):
        for key, value in request.json.items():
            _, mutable = system_config.get_config_privileges(key)
            if mutable and isinstance(value, system_config.get_config_type(key)):
                setattr(system_config, key, value)
        return json(Response.success('修改成功'))
    else:
        return json(Response.invalid('参数无效'))


@config_controller.route('/list', methods=['GET'])
@auth_required
async def list(request: sanic.Request):
    return json(Response.success("", {
        'values': system_config.get_public_config()
    }))
