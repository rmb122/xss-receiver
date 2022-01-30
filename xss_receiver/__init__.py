import sanic

import xss_receiver.response
from xss_receiver.asserts.ip2region import Ip2Region
from xss_receiver.config import Config
from xss_receiver.publish_subscribe import PublishSubscribe, register_publish_subscribe

system_config = Config()
app = sanic.Sanic(__name__)

publish_subscribe = PublishSubscribe(system_config)

from xss_receiver.dnslogger import fork_and_start_listen_dns

if system_config.ENABLE_DNS_LOG:
    fork_and_start_listen_dns((system_config.DNS_LOG_LISTEN_ADDR, 53))

from xss_receiver.database import inject_database_session
from xss_receiver.jwt_auth import install_jwt_auth_middleware

inject_database_session(app)
install_jwt_auth_middleware(app)
register_publish_subscribe(app, publish_subscribe)

from xss_receiver import controllers
