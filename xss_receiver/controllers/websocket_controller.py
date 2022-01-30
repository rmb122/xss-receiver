import asyncio
import typing

import sanic
from sanic import Blueprint
from sanic.server.websockets.impl import WebsocketImplProtocol
from sqlalchemy.future import select

from xss_receiver import publish_subscribe, constants
from xss_receiver.jwt_auth import verify_token
from xss_receiver.models import User
from xss_receiver.publish_subscribe import PublishMessage

websocket_controller = Blueprint('websocket_controller', __name__)

websocket_clients: typing.Set[WebsocketImplProtocol] = set()


@websocket_controller.websocket('/')
async def websocket(request: sanic.Request, ws: WebsocketImplProtocol):
    token = request.args.get('token', None)
    if token is None:
        await ws.close(1000, '无效参数')
        return

    status, user_id = verify_token(token)
    if not status:
        await ws.close(1000, '未登录')
        return

    user = (await request.ctx.db_session.execute(select(User).where(User.user_id == user_id))).scalar()
    if user is None:
        await ws.close(1000, '未登录')
        return

    websocket_clients.add(ws)

    while True:
        try:
            pong_waiter = await ws.ping()
            await asyncio.wait_for(pong_waiter, timeout=constants.WEBSOCKET_TIMEOUT)
            await asyncio.sleep(constants.WEBSOCKET_TIMEOUT)
        except:
            websocket_clients.remove(ws)
            return


async def subscribe_callback(msg: PublishMessage):
    dead_clients = []
    for c in websocket_clients:
        try:
            await c.send(msg.to_json())
        except:
            dead_clients.append(c)

    for c in dead_clients:
        websocket_clients.remove(c)


publish_subscribe.register_callback(constants.PUBLISH_MESSAGE_TYPE_NEW_HTTP_ACCESS_LOG, subscribe_callback)
publish_subscribe.register_callback(constants.PUBLISH_MESSAGE_TYPE_NEW_DNS_LOG, subscribe_callback)
