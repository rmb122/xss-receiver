from math import ceil

import sanic
from sanic import Blueprint

from xss_receiver.database import session_maker
from xss_receiver.jwt_auth import auth_required
from xss_receiver.models import HttpAccessLog
from sqlalchemy.future import select
from sanic.response import json
from xss_receiver.response import Response, PagedResponse

access_log_controller = Blueprint('access_log_controller', __name__)


@access_log_controller.route('/list', methods=['POST'])
@auth_required
def list(request: sanic.Request):
    if isinstance(request.json, dict):
        page = request.json.get('page', 0)
        page_size = request.json.get('page_size', 35)
        filter = request.json.get('filter', {})

        if isinstance(page, int) and isinstance(page_size, int) and isinstance(filter, dict):

            query = select(HttpAccessLog)

            available_filter = {
                'client_ip': HttpAccessLog.client_ip.__eq__,
                'path': HttpAccessLog.path.__eq__,
                'method': HttpAccessLog.method.__eq__,
                'time_before': HttpAccessLog.log_time.__le__,
                'time_after': HttpAccessLog.log_time.__ge__
            }

            for key in filter:
                if isinstance(filter[key], str) and key in available_filter:
                    query = query.filter(available_filter[key](filter[key]))

            access_logs = query.order_by(db.text('-log_id')).offset(page * page_size).limit(page_size).all()
            count = query.count()

            for i in access_logs:
                i.region = get_region_from_ip(i.client_ip, ip2Region)
                i.log_time = i.log_time.strftime('%Y-%m-%d %H:%M:%S')

            paged = PagedResponse(payload=access_logs, total_page=ceil(count / page_size), curr_page=page)
            return json(Response.success('', paged))
        else:
            return json(Response.invalid('无效请求'))
    else:
        return json(Response.invalid('无效请求'))

'''
@access_log_controller.route('/get_last_id', methods=['GET'])
@auth_required
def get_last_id():
    log = db.session.query(AccessLog).order_by(db.text('-log_id')).first()
    if log:
        return jsonify(Response.success('', log.log_id))
    else:
        return jsonify(Response.success('', 0))


@access_log_controller.route('/delete_all', methods=['POST'])
@auth_required
def delete_all():
    if isinstance(request.json, dict):
        delete = request.json.get('delete', None)
        if isinstance(delete, bool) and delete:
            AccessLog.query.delete()
            db.session.commit()
            return jsonify(Response.success('清空成功'))
        else:
            return jsonify(Response.invalid('无效请求'))
    else:
        return jsonify(Response.invalid('无效请求'))
'''