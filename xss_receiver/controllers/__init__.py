import sanic
import sanic.exceptions

from xss_receiver import app, constants
from xss_receiver import system_config
from xss_receiver.database import session_maker
from xss_receiver.utils import add_system_log
from .auth_controller import auth_controller
from .config_controller import config_controller
from .http_access_log_controller import http_access_log_controller
from .http_rule_catalog_controller import http_rule_catalog_controller
from .http_rule_controller import http_rule_controller
from .index_controller import index_controller
from .system_log_controller import system_log_controller
from .temp_file_controller import temp_file_controller
from .upload_file_controller import upload_file_controller
from .websocket_controller import websocket_controller

app.blueprint(config_controller, url_prefix=system_config.URL_PREFIX + '/api/config')
app.blueprint(system_log_controller, url_prefix=system_config.URL_PREFIX + '/api/system_log')
app.blueprint(http_rule_controller, url_prefix=system_config.URL_PREFIX + '/api/http_rule')
app.blueprint(temp_file_controller, url_prefix=system_config.URL_PREFIX + '/api/temp_file')
app.blueprint(http_access_log_controller, url_prefix=system_config.URL_PREFIX + '/api/http_access_log')
app.blueprint(auth_controller, url_prefix=system_config.URL_PREFIX + '/api/auth')
app.blueprint(upload_file_controller, url_prefix=system_config.URL_PREFIX + '/api/upload_file')
app.blueprint(http_rule_catalog_controller, url_prefix=system_config.URL_PREFIX + '/api/http_rule_catalog')
app.blueprint(websocket_controller, url_prefix=system_config.URL_PREFIX + '/api/websocket')
app.blueprint(index_controller, url_prefix='/')

app.static(system_config.URL_PREFIX, system_config.FRONTEND_DIR)


async def server_error_handler(request: sanic.Request, exception):
    if isinstance(exception, sanic.exceptions.FileNotFound):
        return sanic.response.text("", status=404)
    else:
        db_session = session_maker()
        await add_system_log(db_session, f"System error [{str(exception)}] in [{request.path}]", constants.LOG_TYPE_MAIL_SEND_ERROR)
        await db_session.close()

        return sanic.response.text("", status=500)


app.error_handler.add(Exception, server_error_handler)
