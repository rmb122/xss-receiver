from flask import Blueprint, jsonify

from xss_receiver import db
from xss_receiver.jwt_auth import auth_required
from xss_receiver.models import SystemLog
from xss_receiver.response import Response

system_log_controller = Blueprint('system_log_controller', __name__, static_folder=None, template_folder=None)


@system_log_controller.route('/list', methods=['GET'])
@auth_required
def list():
    system_logs = SystemLog.query.order_by(db.text('-log_id')).all()
    for log in system_logs:
        log.log_time = log.log_time.strftime('%Y-%m-%d %H:%M:%S')
    return jsonify(Response.success('', system_logs))
