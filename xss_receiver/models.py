from __future__ import annotations
import datetime
import typing
from dataclasses import dataclass
from sqlalchemy import Column, Text, String, Integer, Boolean, DateTime, VARCHAR, JSON, SmallInteger, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

@dataclass
class HttpRuleCatalog(Base):
    __tablename__ = 'http_rule_catalog'
    catalog_id: int = Column(Integer(), primary_key=True, autoincrement=True)
    catalog_name: str = Column(String(255), unique=True)
    rules: typing.List[HttpRule] = relationship("HttpRule")


@dataclass
class HttpRule(Base):
    __tablename__ = 'http_rule'
    rule_id: int = Column(Integer(), primary_key=True, autoincrement=True)
    path: str = Column(String(255), unique=True)
    filename: str = Column(Text())
    write_log: bool = Column(Boolean())
    send_mail: bool = Column(Boolean())
    comment: str = Column(Text())
    create_time: str = Column(DateTime(), default=datetime.datetime.utcnow)

    catalog_id: str = Column(ForeignKey("http_rule_catalog.catalog_id"))
    catalog: HttpRuleCatalog = relationship("HttpRuleCatalog", back_populates="rules")


@dataclass
class HttpAccessLog(Base):
    __tablename__ = 'http_access_log'
    log_id: int = Column(Integer(), primary_key=True, autoincrement=True)
    path: str = Column(String(255), index=True)
    client_ip: str = Column(VARCHAR(30))
    region: str = Column(VARCHAR(255))
    method: str = Column(VARCHAR(255))
    arg: dict = Column(JSON())
    body: str = Column(Text())
    file: dict = Column(JSON())
    header: dict = Column(JSON())
    body_type: int = Column(SmallInteger())
    log_time: str = Column(DateTime(), default=datetime.datetime.utcnow)


@dataclass
class SystemConfig(Base):
    __tablename__ = 'system_config'
    key: str = Column(String(255), primary_key=True)
    value: str = Column(JSON())


@dataclass
class SystemLog(Base):
    __tablename__ = 'system_log'
    log_id: int = Column(Integer(), primary_key=True, autoincrement=True)
    log_type: int = Column(Integer(), index=True)
    log_content: str = Column(Text())
    log_time: str = Column(DateTime(), default=datetime.datetime.utcnow)


@dataclass
class User(Base):
    __tablename__ = 'user'
    user_id: int = Column(Integer(), primary_key=True, autoincrement=True)
    username: str = Column(String(255), index=True)
    password: str = Column(String(64))
