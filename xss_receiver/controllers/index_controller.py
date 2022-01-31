import asyncio
import typing
from base64 import b64encode
from json import dumps
from os.path import exists, join

import sanic
import sqlalchemy
from sqlalchemy.future import select

from xss_receiver import constants
from xss_receiver import system_config, publish_subscribe
from xss_receiver.constants import ALLOWED_METHODS
from xss_receiver.mailer import send_mail
from xss_receiver.models import HttpRule, HttpAccessLog
from xss_receiver.publish_subscribe import PublishMessage
from xss_receiver.utils import process_headers, random_string, fix_upper_case, write_file, filter_list, render_dynamic_template, read_file, generate_dynamic_template_globals, add_system_log, secure_filename_with_directory

index_controller = sanic.Blueprint('index_controller', __name__)


@index_controller.route('/', methods=ALLOWED_METHODS)
@index_controller.route('/<path:path>', methods=ALLOWED_METHODS)
@process_headers
async def mapping(request: sanic.Request, path=''):
    path = request.path
    result: sqlalchemy.engine.result.ChunkedIteratorResult
    result = await request.ctx.db_session.execute(select(HttpRule).where(HttpRule.path == path))
    rule = result.scalar()

    if rule is None:
        return sanic.response.html('', 404)

    if system_config.BEHIND_PROXY:
        client_ip = request.headers.get(constants.REAL_IP_HEADER, 'Header not found')
    else:
        client_ip = request.ip

    method = request.method
    header = fix_upper_case(dict(request.headers))
    arg = filter_list(dict(request.args))
    file = {}
    raw_body_str = request.body.decode('utf-8', 'ignore')

    content_type = request.headers.get('Content-Type', '').lower()
    if content_type[:19] == 'multipart/form-data':
        body_type = constants.BODY_TYPE_NORMAL
        body = dumps(filter_list(dict(request.form)))

        for file_key in request.files:
            # 只保存同名的第一个文件
            if len(request.files[file_key]) > 0:
                upload_file = request.files[file_key][0]
                if system_config.TEMP_FILE_SAVE:
                    save_name = random_string(32)
                    asyncio.create_task(write_file(join(system_config.TEMP_FILE_PATH, save_name), upload_file.body))
                else:
                    save_name = None
                file[file_key] = {'filename': upload_file.name, 'save_name': save_name}
    else:
        body = request.body
        try:
            body = body.decode('utf-8')
            body_type = constants.BODY_TYPE_NORMAL
        except UnicodeDecodeError:
            body = b64encode(body).decode()
            body_type = constants.BODY_TYPE_ESCAPED

    if rule.write_log:
        if len(body) > system_config.MAX_TEMP_UPLOAD_SIZE:
            body = ""
            body_type = constants.BODY_TYPE_TOO_LONG

        access_log = HttpAccessLog(path=path, client_ip=client_ip, method=method, arg=arg,
                                   body=body, file=file, header=header, body_type=body_type)

        request.ctx.db_session.add(access_log)
        await request.ctx.db_session.commit()

        message = PublishMessage(msg_type=constants.PUBLISH_MESSAGE_TYPE_NEW_HTTP_ACCESS_LOG, msg_content=path)
        publish_subscribe.publish(message)

    if rule.send_mail:
        asyncio.create_task(send_mail(path, f"Client IP: {client_ip}\n\n"
                                            f"Header: {dumps(dict(request.headers), indent=4)}\n\n"
                                            f"Args: {dumps(dict(request.args), indent=4)}\n\n"
                                            f"Body: {raw_body_str}"))

    filename = secure_filename_with_directory(rule.filename)
    filepath = join(system_config.UPLOAD_PATH, filename)
    if exists(filepath):
        if rule.rule_type == constants.RULE_TYPE_DYNAMIC_TEMPLATE:
            response = sanic.HTTPResponse('', 200, {}, 'text/html; charset=utf-8')
            extra_output = []
            _globals = generate_dynamic_template_globals(system_config, request, response, client_ip, path, method, header, arg, raw_body_str, file, extra_output)
            template_result, error = await render_dynamic_template((await read_file(filepath)).decode(), _globals)
            response.body = template_result.encode() + b''.join(extra_output)

            if error is not None:
                log_content = f'Template render error [{error}] in [{path}]'
                await add_system_log(request.ctx.db_session, log_content, constants.LOG_TYPE_LOGIN)

        elif rule.rule_type == constants.RULE_TYPE_STATIC_FILE:
            response = await sanic.response.file(filepath)
        else:
            response = sanic.response.html('', 404)
    else:
        response = sanic.response.html('', 404)

    return response
