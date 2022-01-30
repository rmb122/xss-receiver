from math import ceil

import sanic
from sanic import Blueprint
from sanic.response import json
from sqlalchemy import func, delete
from sqlalchemy.future import select

from xss_receiver.jwt_auth import auth_required
from xss_receiver.models import DNSLog
from xss_receiver.response import Response, PagedResponse
from xss_receiver.utils import get_region_from_ip

dns_log_controller = Blueprint('dns_log_controller', __name__)


@dns_log_controller.route('/list', methods=['POST'])
@auth_required
async def dns_log_list(request: sanic.Request):
    if isinstance(request.json, dict):
        page = request.json.get('page', 0)
        page_size = request.json.get('page_size', 35)
        filter = request.json.get('filter', {})

        if isinstance(page, int) and isinstance(page_size, int) and isinstance(filter, dict):
            query = select(DNSLog)
            count_query = select(func.count('1')).select_from(DNSLog)

            available_filter = {
                'client_ip': DNSLog.client_ip.__eq__,
                'domain': DNSLog.domain.__eq__,
                'dns_type': DNSLog.dns_type.__eq__,
                'time_before': DNSLog.log_time.__le__,
                'time_after': DNSLog.log_time.__ge__
            }

            for key in filter:
                if isinstance(filter[key], (str, int)) and key in available_filter:
                    query = query.where(available_filter[key](filter[key]))
                    count_query = count_query.where(available_filter[key](filter[key]))

            dns_log_scalars = (await request.ctx.db_session.execute(
                query.order_by(DNSLog.log_id.desc()).offset(page * page_size).limit(page_size)
            )).scalars()
            count = (await request.ctx.db_session.execute(
                count_query
            )).scalar()

            dns_logs = []
            for i in dns_log_scalars:
                # 也可以在入库的时候计算地区, 在这里输出时计算是因为感觉存储大量地址挺浪费空间的 233, 而计算不用太耗时间
                i.region = get_region_from_ip(i.client_ip)
                i.log_time = i.log_time.strftime('%Y-%m-%d %H:%M:%S')
                dns_logs.append(i)

            paged = PagedResponse(payload=dns_logs, total_page=ceil(count / page_size), curr_page=page)
            return json(Response.success('', paged))
        else:
            return json(Response.invalid('无效请求'))
    else:
        return json(Response.invalid('无效请求'))


@dns_log_controller.route('/get_last_id', methods=['GET'])
@auth_required
async def get_last_id(request: sanic.Request):
    query = select(DNSLog).order_by(DNSLog.log_id.desc())
    log = (await request.ctx.db_session.execute(query)).scalar()
    if log:
        return json(Response.success('', log.log_id))
    else:
        return json(Response.success('', 0))


@dns_log_controller.route('/delete_all', methods=['POST'])
@auth_required
async def delete_all(request: sanic.Request):
    if isinstance(request.json, dict):
        delete_check = request.json.get('delete', False)
        if isinstance(delete_check, bool) and delete_check:
            await request.ctx.db_session.execute(delete(DNSLog))
            await request.ctx.db_session.commit()
            return json(Response.success('清空成功'))
        else:
            return json(Response.invalid('无效请求'))
    else:
        return json(Response.invalid('无效请求'))
