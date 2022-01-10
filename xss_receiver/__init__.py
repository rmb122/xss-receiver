from os import path

import sanic

from xss_receiver.asserts.ip2region import Ip2Region
from xss_receiver.config import Config

app = sanic.Sanic(__name__)
system_config = Config()

ip2region = Ip2Region(f'{path.dirname(__file__)}/asserts/ip2region.db')


from xss_receiver import jwt_auth
# from xss_receiver import controllers

@app.route('/login')
def login(request: sanic.Request):
    return sanic.response.text(jwt_auth.sign_token())


@app.route('/')
@jwt_auth.auth_required
def index(request: sanic.Request):
    return sanic.response.text('asd')
