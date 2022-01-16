import sanic

from xss_receiver import app
from xss_receiver import system_config
from .auth_controller import auth_controller
from .config_controller import config_controller
from .http_access_log_controller import http_access_log_controller
from .http_rule_controller import http_rule_controller
from .index_controller import index_controller
from .system_log_controller import system_log_controller
from .temp_file_controller import temp_file_controller
from .upload_file_controller import upload_file_controller
from .http_rule_catalog_controller import http_rule_catalog_controller

app.blueprint(config_controller, url_prefix=system_config.URL_PREFIX + '/api/config')
app.blueprint(system_log_controller, url_prefix=system_config.URL_PREFIX + '/api/system_log')
app.blueprint(http_rule_controller, url_prefix=system_config.URL_PREFIX + '/api/http_rule')
app.blueprint(temp_file_controller, url_prefix=system_config.URL_PREFIX + '/api/temp_file')
app.blueprint(http_access_log_controller, url_prefix=system_config.URL_PREFIX + '/api/http_access_log')
app.blueprint(auth_controller, url_prefix=system_config.URL_PREFIX + '/api/auth')
app.blueprint(upload_file_controller, url_prefix=system_config.URL_PREFIX + '/api/upload_file')
app.blueprint(http_rule_catalog_controller, url_prefix=system_config.URL_PREFIX + '/api/http_rule_catalog')
app.blueprint(index_controller, url_prefix='/')


async def server_error_handler(request, exception):
    return sanic.response.text("Oops :(", status=500)

# app.error_handler.add(Exception, server_error_handler)
