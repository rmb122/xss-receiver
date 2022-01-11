from math import ceil

import sanic
from sanic import Blueprint
from sanic.response import json
from sqlalchemy import func, delete
from sqlalchemy.future import select

from xss_receiver import ip2region
from xss_receiver.jwt_auth import auth_required
from xss_receiver.models import HttpAccessLog
from xss_receiver.response import Response, PagedResponse
from xss_receiver.utils import get_region_from_ip

access_log_controller = Blueprint('access_log_controller', __name__)


@access_log_controller.route('/list', methods=['POST'])
@auth_required
async def list(request: sanic.Request):
    if isinstance(request.json, dict):
        page = request.json.get('page', 0)
        page_size = request.json.get('page_size', 35)
        filter = request.json.get('filter', {})

        if isinstance(page, int) and isinstance(page_size, int) and isinstance(filter, dict):
            query = select(HttpAccessLog)
            count_query = select(func.count('1')).select_from(HttpAccessLog)

            available_filter = {
                'client_ip': HttpAccessLog.client_ip.__eq__,
                'path': HttpAccessLog.path.__eq__,
                'method': HttpAccessLog.method.__eq__,
                'time_before': HttpAccessLog.log_time.__le__,
                'time_after': HttpAccessLog.log_time.__ge__
            }

            for key in filter:
                if isinstance(filter[key], str) and key in available_filter:
                    query = query.where(available_filter[key](filter[key]))
                    count_query = count_query.where(available_filter[key](filter[key]))

            access_log_scalars = (await request.ctx.db_session.execute(
                query.order_by(HttpAccessLog.log_id.desc()).offset(page * page_size).limit(page_size)
            )).scalars()
            count = (await request.ctx.db_session.execute(
                count_query
            )).scalar()

            access_logs = []
            for i in access_log_scalars:
                # 也可以在入库的时候计算地区, 在这里输出时计算是因为感觉存储大量地址挺浪费空间的 233, 而计算不用太耗时间
                i.region = get_region_from_ip(i.client_ip, ip2region)
                i.log_time = i.log_time.strftime('%Y-%m-%d %H:%M:%S')
                access_logs.append(i)

            paged = PagedResponse(payload=access_logs, total_page=ceil(count / page_size), curr_page=page)
            return json(Response.success('', paged))
        else:
            return json(Response.invalid('无效请求'))
    else:
        return json(Response.invalid('无效请求'))


@access_log_controller.route('/get_last_id', methods=['GET'])
@auth_required
async def get_last_id(request: sanic.Request):
    query = select(HttpAccessLog).order_by(HttpAccessLog.log_id.desc())
    log = (await request.ctx.db_session.execute(query)).scalar()
    if log:
        return json(Response.success('', log.log_id))
    else:
        return json(Response.success('', 0))


@access_log_controller.route('/delete_all', methods=['POST'])
@auth_required
async def delete_all(request: sanic.Request):
    if isinstance(request.json, dict):
        delete_check = request.json.get('delete', False)
        if isinstance(delete_check, bool) and delete_check:
            await request.ctx.db_session.execute(delete(HttpAccessLog))
            await request.ctx.db_session.commit()
            return json(Response.success('清空成功'))
        else:
            return json(Response.invalid('无效请求'))
    else:
        return json(Response.invalid('无效请求'))
