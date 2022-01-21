import sanic

import xss_receiver.response
from xss_receiver.asserts.ip2region import Ip2Region
from xss_receiver.config import Config
from xss_receiver.publish_subscribe import PublishSubscribe, register_publish_subscribe

system_config = Config()
publish_subscribe = PublishSubscribe()

app = sanic.Sanic(__name__)

from xss_receiver.database import inject_database_session
from xss_receiver.jwt_auth import install_jwt_auth_middleware

inject_database_session(app)
install_jwt_auth_middleware(app)
register_publish_subscribe(app, publish_subscribe)

from xss_receiver import controllers
