import datetime
from dataclasses import dataclass

from xss_receiver import db


@dataclass
class SystemLog(db.Model):
    __tablename__ = 'system_logs'
    log_id: int = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    log_content: str = db.Column(db.TEXT())
    log_time: str = db.Column(db.DateTime(), default=datetime.datetime.utcnow)


@dataclass
class Rule(db.Model):
    __tablename__ = 'rules'
    rule_id: int = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    path: str = db.Column(db.String(255), unique=True)
    filename: str = db.Column(db.Text())
    write_log: bool = db.Column(db.Boolean())
    send_mail: bool = db.Column(db.Boolean())
    comment: str = db.Column(db.Text())
    create_time: str = db.Column(db.DateTime(), default=datetime.datetime.utcnow)


@dataclass
class AccessLog(db.Model):
    __tablename__ = 'access_logs'
    region: str
    log_id: int = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    path: str = db.Column(db.String(255), index=True)
    client_ip: str = db.Column(db.VARCHAR(30))
    method: str = db.Column(db.VARCHAR(255))
    arg: dict = db.Column(db.JSON())
    body: str = db.Column(db.Text())
    file: dict = db.Column(db.JSON())
    header: dict = db.Column(db.JSON())
    body_type: int = db.Column(db.SmallInteger())
    log_time: str = db.Column(db.DateTime(), default=datetime.datetime.utcnow)
