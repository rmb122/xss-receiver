from sys import modules
# from xss_receiver import jwt_auth
import sanic
from xss_receiver.config import Config
from xss_receiver.asserts.ip2region import Ip2Region

app = sanic.Sanic(__name__)
config = Config()

'''

ip2Region = Ip2Region(f'{app.root_path}/asserts/ip2region.db')

from xss_receiver.CachedConfig import CachedConfig

cached_config = CachedConfig()

from xss_receiver import models

db.create_all()

from xss_receiver import controllers
'''