import sanic
from sanic import Blueprint, json

from xss_receiver.jwt_auth import auth_required
from xss_receiver.models import SystemLog
from sqlalchemy.future import select
from sqlalchemy import func
from xss_receiver.response import Response, PagedResponse
from math import ceil

system_log_controller = Blueprint('system_log_controller', __name__)


@system_log_controller.route('/list', methods=['POST'])
@auth_required
async def system_log_list(request: sanic.Request):
    if isinstance(request.json, dict):
        page = request.json.get('page', 0)
        page_size = request.json.get('page_size', 35)
        filter = request.json.get('filter', {})

        if isinstance(page, int) and isinstance(page_size, int) and isinstance(filter, dict):
            system_log_scalars = (await request.ctx.db_session.execute(
                select(SystemLog).order_by(SystemLog.log_id.desc()).offset(page * page_size).limit(page_size)
            )).scalars()

            count = (await request.ctx.db_session.execute(
                select(func.count('1')).select_from(SystemLog)
            )).scalar()

            system_logs = []
            for log in system_log_scalars:
                log.log_time = log.log_time.strftime('%Y-%m-%d %H:%M:%S')
                system_logs.append(log)

            paged = PagedResponse(payload=system_logs, total_page=ceil(count / page_size), curr_page=page)
            return json(Response.success('', paged))

        else:
            return json(Response.invalid('无效参数'))
    else:
        return json(Response.invalid('无效参数'))
