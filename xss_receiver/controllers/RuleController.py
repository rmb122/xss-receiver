from flask import Blueprint, request, jsonify

from xss_receiver import db
from xss_receiver.JWTAuth import auth_required
from xss_receiver.Models import Rule
from xss_receiver.Response import Response

rule_controller = Blueprint('rule_controller', __name__, static_folder=None, template_folder=None)


@rule_controller.route('/add', methods=['POST'])
@auth_required
def add():
    if isinstance(request.json, dict):
        path = request.json.get('path', None)
        filename = request.json.get('filename', None)
        write_log = request.json.get('write_log', None)
        send_mail = request.json.get('send_mail', None)
        comment = request.json.get('comment', None)

        if isinstance(path, str) and isinstance(filename, str) and isinstance(write_log, bool) and isinstance(send_mail, bool) and isinstance(comment, str):
            rule = Rule.query.filter_by(path=path).first()
            if rule is None:
                rule = Rule(path=path, filename=filename, write_log=write_log, send_mail=send_mail, comment=comment)
                db.session.add(rule)
                db.session.commit()
                return jsonify(Response.success('添加成功'))
            else:
                return jsonify(Response.failed('已经存在此规则'))
        else:
            return jsonify(Response.invalid('参数无效'))
    else:
        return jsonify(Response.invalid('参数无效'))


@rule_controller.route('/modify', methods=['POST'])
@auth_required
def modify():
    if isinstance(request.json, dict):
        rule_id = request.json.get('rule_id', None)
        path = request.json.get('path', None)
        filename = request.json.get('filename', None)
        write_log = request.json.get('write_log', None)
        send_mail = request.json.get('send_mail', None)
        comment = request.json.get('comment', None)

        if isinstance(rule_id, int):
            rule = Rule.query.filter_by(rule_id=rule_id).first()
            if rule is not None:
                if isinstance(path, str):
                    rule.path = path
                if isinstance(filename, str):
                    rule.filename = filename
                if isinstance(write_log, bool):
                    rule.write_log = write_log
                if isinstance(send_mail, bool):
                    rule.send_mail = send_mail
                if isinstance(comment, str):
                    rule.comment = comment

                db.session.add(rule)
                db.session.commit()
                return jsonify(Response.success('修改成功'))
            else:
                return jsonify(Response.failed('规则不存在'))
        else:
            return jsonify(Response.invalid('参数无效'))
    else:
        return jsonify(Response.invalid('参数无效'))


@rule_controller.route('/delete', methods=['POST'])
@auth_required
def delete():
    if isinstance(request.json, dict):
        rule_id = request.json.get('rule_id', None)

        if isinstance(rule_id, int):
            rule = Rule.query.filter_by(rule_id=rule_id).first()
            if rule is not None:
                db.session.delete(rule)
                db.session.commit()
                return jsonify(Response.success('删除成功'))
            else:
                return jsonify(Response.failed('规则不存在'))
        else:
            return jsonify(Response.invalid('参数无效'))
    else:
        return jsonify(Response.invalid('参数无效'))


@rule_controller.route('/list', methods=['GET'])
@auth_required
def list():
    rule_list = Rule.query.all()
    for rule in rule_list:
        rule.create_time = rule.create_time.strftime('%Y-%m-%d %H:%M:%S')
    return jsonify(Response.success('', rule_list))
