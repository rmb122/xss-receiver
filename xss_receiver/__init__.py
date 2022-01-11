from os import path

import sanic

import xss_receiver.response
from xss_receiver.asserts.ip2region import Ip2Region
from xss_receiver.database import inject_database_session
from xss_receiver.config import Config

app = sanic.Sanic(__name__)

inject_database_session(app)
system_config = Config()
ip2region = Ip2Region(f'{path.dirname(__file__)}/asserts/ip2region.db')

from xss_receiver import controllers
