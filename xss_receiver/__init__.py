from sys import modules
# from xss_receiver import jwt_auth
import sanic
from xss_receiver.config import Config
from xss_receiver.asserts.ip2region import Ip2Region

app = sanic.Sanic(__name__)
config = Config()

import xss_receiver.response

@app.route('/')
def index(request):
    print(config.RECV_MAIL_ADDR)
    return sanic.response.text('123')


@app.route('/set', methods=["POST"])
def set(request: sanic.Request):
    config.RECV_MAIL_ADDR = request.form['asd']
    return sanic.response.text('123')

'''

ip2Region = Ip2Region(f'{app.root_path}/asserts/ip2region.db')

from xss_receiver.CachedConfig import CachedConfig

cached_config = CachedConfig()

from xss_receiver import models

db.create_all()

from xss_receiver import controllers
'''