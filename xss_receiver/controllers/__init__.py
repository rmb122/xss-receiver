from xss_receiver.config import URL_PREFIX

from xss_receiver import app
from .AccessLogController import access_log_controller
from .AuthController import auth_controller
from .ConfigController import config_controller
from .IndexController import index_controller
from .RuleController import rule_controller
from .SystemlogController import system_log_controller
from .TempFileController import temp_file_controller
from .UploadFileController import upload_file_controller

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
