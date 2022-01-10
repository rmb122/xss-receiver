from xss_receiver.config import URL_PREFIX

from xss_receiver import app
from .access_log_controller import access_log_controller
from .auth_controller import auth_controller
from .config_controller import config_controller
from .index_controller import index_controller
from .rule_controller import rule_controller
from .system_log_controller import system_log_controller
from .temp_file_controller import temp_file_controller
from .upload_file_controller import upload_file_controller

app.register_blueprint(config_controller, url_prefix=URL_PREFIX + '/api/config')
app.register_blueprint(system_log_controller, url_prefix=URL_PREFIX + '/api/system_log')
app.register_blueprint(rule_controller, url_prefix=URL_PREFIX + '/api/rule')
app.register_blueprint(temp_file_controller, url_prefix=URL_PREFIX + '/api/temp_file')
app.register_blueprint(access_log_controller, url_prefix=URL_PREFIX + '/api/access_log')
app.register_blueprint(auth_controller, url_prefix=URL_PREFIX + '/api/auth')
app.register_blueprint(upload_file_controller, url_prefix=URL_PREFIX + '/api/file')
app.register_blueprint(index_controller, url_prefix='/')


@app.errorhandler(500)
def error(e):
    print(e)
    return '', 200
