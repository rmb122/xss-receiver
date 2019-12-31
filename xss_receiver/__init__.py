from sys import modules

from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy

from xss_receiver import JWTAuth
from xss_receiver.Config import URL_PREFIX
from xss_receiver.Utils import NoServerHeaderFlask
from xss_receiver.asserts.ip2region import Ip2Region

app = NoServerHeaderFlask(__name__, static_folder=None, template_folder=None)
app.config.from_pyfile('Config.py')
app.config['SESSION_COOKIE_PATH'] = f'{URL_PREFIX}/admin/'
JWTAuth.init_app(app)
cache = Cache()

if modules.get('uwsgi'):
    cache.init_app(app, config={'CACHE_TYPE': 'uwsgi', 'CACHE_UWSGI_NAME': 'xss', 'CACHE_DEFAULT_TIMEOUT': 0})
else:
    cache.init_app(app, config={'CACHE_TYPE': 'filesystem', 'CACHE_DIR': '/dev/shm/', 'CACHE_OPTIONS': {'mode': 0o600}, 'CACHE_DEFAULT_TIMEOUT': 0})

db = SQLAlchemy(app)
ip2Region = Ip2Region(f'{app.root_path}/asserts/ip2region.db')

from xss_receiver.CachedConfig import CachedConfig

cached_config = CachedConfig()

from xss_receiver import Models

db.create_all()

from xss_receiver import controllers
