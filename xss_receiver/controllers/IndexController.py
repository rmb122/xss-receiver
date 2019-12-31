from base64 import b64encode
from json import dumps
from os.path import exists, join

from flask import Blueprint, request, send_file
from werkzeug.utils import secure_filename
from xss_receiver.Config import ALLOWED_METHODS, UPLOAD_PATH, BEHIND_PROXY, TEMP_FILE_PATH

from xss_receiver import Constants
from xss_receiver import db, cached_config
from xss_receiver.Mailer import Mailer
from xss_receiver.Models import AccessLog, Rule
from xss_receiver.Utils import file_nocache, random_string

index_controller = Blueprint('index_controller', __name__, static_folder=None, template_folder=None)


@index_controller.route('/', methods=ALLOWED_METHODS)
@index_controller.route('/<path:path>', methods=ALLOWED_METHODS)
@file_nocache
def mapping(path=''):
    path = request.path
    rule = Rule.query.filter_by(path=path).first()
    if rule:
        if BEHIND_PROXY:
            client_ip = request.headers.get('X-Real-IP', 'Header not found')
        else:
            client_ip = request.remote_addr

        if rule.write_log:
            method = request.method
            header = dict(request.headers)
            arg = dict(request.args)
            file = {}
            body_type = Constants.BODY_TYPE_NORMAL

            content_type = request.headers.get('Content-Type', '').lower()
            if content_type[:19] == 'multipart/form-data':
                body = dumps(dict(request.form))
                file = {}

                if cached_config.TEMP_FILE_SAVE:
                    for file_key in request.files:
                        save_name = random_string(32)
                        file[file_key] = {'filename': request.files[file_key].filename, 'save_name': save_name}
                        request.files[file_key].save(join(TEMP_FILE_PATH, save_name))
                else:
                    for file_key in request.files:
                        file[file_key] = {'filename': request.files[file_key].filename, 'save_name': None}

            else:
                body = request.get_data()
                try:
                    body = body.decode('utf-8')
                except UnicodeDecodeError:
                    body_type = Constants.BODY_TYPE_ESCAPED
                    body = b64encode(body).decode()

            if len(body) > 65000:
                body_type = Constants.BODY_TYPE_TOO_LONG
                body = ""

            access_log = AccessLog(path=path, client_ip=client_ip, method=method, arg=arg, body=body, file=file,
                                   header=header, body_type=body_type)
            db.session.add(access_log)
            db.session.commit()

        if rule.send_mail:
            Mailer.send_mail(path, f"Client IP: {client_ip}\n\n"
                                   f"Header: {dumps(dict(request.headers), indent=4)}\n\n"
                                   f"Args: {dumps(dict(request.args), indent=4)}")

        filename = secure_filename(rule.filename)
        filepath = join(UPLOAD_PATH, filename)
        if exists(filepath):
            response = send_file(filepath)
        else:
            response = ('', 404)
    else:
        response = ('', 404)
    return response
