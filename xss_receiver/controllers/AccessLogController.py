from math import ceil

from flask import Blueprint, request, jsonify

from xss_receiver import db, ip2Region
from xss_receiver.JWTAuth import auth_required
from xss_receiver.Models import AccessLog
from xss_receiver.Response import Response, PagedResponse

access_log_controller = Blueprint('access_log_controller', __name__, static_folder=None, template_folder=None)


def format_region(region):
    try:
        region = region['region'].decode()
        region = region.split('|')
        tmp = []
        for k in region:
            if k != '0':
                tmp.append(k)
            if k == '内网IP':
                return '局域网'
        return ''.join(tmp)
    except Exception:
        return '解析错误'


def get_region_from_ip(ip, ip2Region):
    if ":" not in ip:
        region = ""
        retry = 0
        while not region and retry < 3:
            try:
                region = ip2Region.btreeSearch(ip)
            except Exception:
                retry += 1
                pass
        if region == "":
            return "转换中出错"
        return format_region(region)
    else:
        return "不支持 IPv6 查询"


@access_log_controller.route('/list', methods=['POST'])
@auth_required
def list():
    if isinstance(request.json, dict):
        page = request.json.get('page', None)
        page_size = request.json.get('page_size', None)
        filter = request.json.get('filter', None)

        if page is None:
            page = 0
        if page_size is None:
            page_size = 35
        if filter is None:
            filter = {}

        if isinstance(page, int) and isinstance(page_size, int) and isinstance(filter, dict):
            query = db.session.query(AccessLog)

            available_filter = {
                'client_ip': AccessLog.client_ip.__eq__,
                'path': AccessLog.path.__eq__,
                'method': AccessLog.method.__eq__,
                'time_before': AccessLog.log_time.__le__,
                'time_after': AccessLog.log_time.__ge__
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
            return jsonify(Response.success('', paged))
        else:
            return jsonify(Response.invalid('无效请求'))
    else:
        return jsonify(Response.invalid('无效请求'))


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
