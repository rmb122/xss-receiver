import sanic
from sanic import Blueprint
from sanic.response import json
from sqlalchemy.future import select

from xss_receiver.jwt_auth import auth_required
from xss_receiver.models import HttpRuleCatalog, HttpRule
from xss_receiver.response import Response

http_rule_catalog_controller = Blueprint('http_rule_catalog_controller', __name__)


@http_rule_catalog_controller.route('/add', methods=['POST'])
@auth_required
async def add_catalog(request: sanic.Request):
    if isinstance(request.json, dict):
        catalog_name = request.json.get('catalog_name', None)

        if isinstance(catalog_name, str):
            query = select(HttpRuleCatalog).where(HttpRuleCatalog.catalog_name == catalog_name)
            catalog = (await request.ctx.db_session.execute(query)).scalar()
            if catalog is None:
                catalog = HttpRuleCatalog(catalog_name=catalog_name)
                request.ctx.db_session.add(catalog)
                await request.ctx.db_session.commit()
                return json(Response.success('创建成功'))
            else:
                return json(Response.failed('已有此分类'))
        else:
            return json(Response.invalid('参数无效'))
    else:
        return json(Response.invalid('参数无效'))


@http_rule_catalog_controller.route('/delete', methods=['POST'])
@auth_required
async def delete_catalog(request: sanic.Request):
    if isinstance(request.json, dict):
        catalog_id = request.json.get('catalog_id', None)

        if isinstance(catalog_id, int):
            query = select(HttpRuleCatalog).where(HttpRuleCatalog.catalog_id == catalog_id)
            catalog = (await request.ctx.db_session.execute(query)).scalar()
            if catalog is not None:
                # 删除分类和其下的所有规则
                query = select(HttpRule).where(HttpRule.catalog_id == catalog_id)

                rules = (await request.ctx.db_session.execute(query)).scalars()
                for rule in rules:
                    await request.ctx.db_session.delete(rule)
                await request.ctx.db_session.delete(catalog)
                await request.ctx.db_session.commit()
                return json(Response.success('删除成功'))
            else:
                return json(Response.failed('分类不存在'))
        else:
            return json(Response.invalid('参数无效'))
    else:
        return json(Response.invalid('参数无效'))


@http_rule_catalog_controller.route('/list')
@auth_required
async def catalog_list(request: sanic.Request):
    catalogs = (await request.ctx.db_session.execute(select(HttpRuleCatalog))).scalars()
    catalogs = list(catalogs)
    return json(Response.success('', catalogs))
