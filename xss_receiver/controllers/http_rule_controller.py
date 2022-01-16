import sanic
from sanic import Blueprint, json
from sqlalchemy.future import select

from xss_receiver import constants
from xss_receiver.jwt_auth import auth_required
from xss_receiver.models import HttpRule, HttpRuleCatalog
from xss_receiver.response import Response

http_rule_controller = Blueprint('http_rule_controller', __name__)


@http_rule_controller.route('/add', methods=['POST'])
@auth_required
async def add(request: sanic.Request):
    if isinstance(request.json, dict):
        path = request.json.get('path', None)
        rule_type = request.json.get('rule_type', None)
        filename = request.json.get('filename', None)
        write_log = request.json.get('write_log', None)
        send_mail = request.json.get('send_mail', None)
        comment = request.json.get('comment', None)
        catalog_id = request.json.get('catalog_id', None)

        if isinstance(path, str) and isinstance(filename, str) and isinstance(write_log, bool) \
                and isinstance(send_mail, bool) and isinstance(comment, str) and isinstance(catalog_id, int) and rule_type in constants.RULE_TYPES:
            query = select(HttpRuleCatalog).where(HttpRuleCatalog.catalog_id == catalog_id)
            catalog = (await request.ctx.db_session.execute(query)).scalar()
            if catalog is not None:
                query = select(HttpRule).where(HttpRule.path == path)
                rule = (await request.ctx.db_session.execute(query)).scalar()
                if rule is None:
                    rule = HttpRule(path=path, rule_type=rule_type, filename=filename, write_log=write_log, send_mail=send_mail, comment=comment, catalog_id=catalog_id)
                    request.ctx.db_session.add(rule)
                    await request.ctx.db_session.commit()
                    return json(Response.success('添加成功'))
                else:
                    return json(Response.failed('已经存在此规则'))
            else:
                return json(Response.failed('分类不存在'))
        else:
            return json(Response.invalid('参数无效'))
    else:
        return json(Response.invalid('参数无效'))


@http_rule_controller.route('/modify', methods=['POST'])
@auth_required
async def modify(request: sanic.Request):
    if isinstance(request.json, dict):
        rule_id = request.json.get('rule_id', None)
        rule_type = request.json.get('rule_type', None)
        path = request.json.get('path', None)
        filename = request.json.get('filename', None)
        write_log = request.json.get('write_log', None)
        send_mail = request.json.get('send_mail', None)
        comment = request.json.get('comment', None)
        catalog_id = request.json.get('catalog_id', None)

        if isinstance(rule_id, int):
            query = select(HttpRule).where(HttpRule.rule_id == rule_id)
            rule = (await request.ctx.db_session.execute(query)).scalar()
            if rule is not None:
                if isinstance(path, str):
                    query = select(HttpRule).where(HttpRule.path == path)
                    result = (await request.ctx.db_session.execute(query)).scalar()
                    if result is None or result.rule_id == rule_id:
                        rule.path = path
                    else:
                        return json(Response.failed('路径已经存在'))

                if isinstance(catalog_id, int):
                    query = select(HttpRuleCatalog).where(HttpRuleCatalog.catalog_id == catalog_id)
                    result = (await request.ctx.db_session.execute(query)).scalar()
                    if result is not None:
                        rule.catalog_id = catalog_id
                    else:
                        return json(Response.failed('分类不存在'))

                if isinstance(filename, str):
                    rule.filename = filename
                if isinstance(write_log, bool):
                    rule.write_log = write_log
                if isinstance(send_mail, bool):
                    rule.send_mail = send_mail
                if isinstance(comment, str):
                    rule.comment = comment
                if rule_type in constants.RULE_TYPES:
                    rule.rule_type = rule_type

                request.ctx.db_session.add(rule)
                await request.ctx.db_session.commit()
                return json(Response.success('修改成功'))
            else:
                return json(Response.failed('规则不存在'))
        else:
            return json(Response.invalid('参数无效'))
    else:
        return json(Response.invalid('参数无效'))


@http_rule_controller.route('/delete', methods=['POST'])
@auth_required
async def delete(request: sanic.Request):
    if isinstance(request.json, dict):
        rule_id = request.json.get('rule_id', None)

        if isinstance(rule_id, int):
            query = select(HttpRule).where(HttpRule.rule_id == rule_id)
            rule = (await request.ctx.db_session.execute(query)).scalar()

            if rule is not None:
                await request.ctx.db_session.delete(rule)
                await request.ctx.db_session.commit()
                return json(Response.success('删除成功'))
            else:
                return json(Response.failed('规则不存在'))
        else:
            return json(Response.invalid('参数无效'))
    else:
        return json(Response.invalid('参数无效'))


@http_rule_controller.route('/list', methods=['GET'])
@auth_required
async def http_rule_list(request: sanic.Request):
    rules = (await request.ctx.db_session.execute(select(HttpRule))).scalars()
    rules = list(rules)

    # for rule in rules:
    #    rule.create_time = rule.create_time.strftime('%Y-%m-%d %H:%M:%S')
    return json(Response.success('', rules))
