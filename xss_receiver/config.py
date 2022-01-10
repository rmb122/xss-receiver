import asyncio
import json
import multiprocessing
import os
import typing

import sqlalchemy
from sqlalchemy.future import select

from xss_receiver import constants
from xss_receiver.database import session_maker, engine
from xss_receiver.models import SystemConfig

_manager = multiprocessing.Manager()
_CONFIG_CACHE = _manager.dict()


class Config:
    # name, from_env
    _CONFIG_KEYS: typing.Dict[str, bool] = {
        'LOGIN_SALT': True,
        'SECRET_KEY': True,
        'URL_PREFIX': True,
        'BEHIND_PROXY': True,
        'UPLOAD_PATH': True,
        'TEMP_FILE_PATH': True,

        'TEMP_FILE_SAVE': False,
        'RECV_MAIL_ADDR': False,
        'SEND_MAIL_ADDR': False,
        'SEND_MAIL_PASSWD': False,
        'SEND_MAIL_SMTP_HOST': False,
        'SEND_MAIL_SMTP_PORT': False,
        'SEND_MAIL_SMTP_SSL': False,
        'MAX_PREVIEW_SIZE': False,
        'MAX_TEMP_UPLOAD_SIZE': False
    }

    _CONFIG_DEFAULTS: typing.Dict[str, typing.Union[str, bool, int]] = {
        'LOGIN_SALT': '',
        'SECRET_KEY': os.urandom(32),
        'URL_PREFIX': '',
        'BEHIND_PROXY': False,
        'UPLOAD_PATH': '/tmp',
        'TEMP_FILE_PATH': '/tmp',

        'TEMP_FILE_SAVE': False,
        'RECV_MAIL_ADDR': '',
        'SEND_MAIL_ADDR': '',
        'SEND_MAIL_PASSWD': '',
        'SEND_MAIL_SMTP_HOST': '',
        'SEND_MAIL_SMTP_PORT': 465,
        'SEND_MAIL_SMTP_SSL': True,
        'MAX_PREVIEW_SIZE': 1048576,
        'MAX_TEMP_UPLOAD_SIZE': 1048576
    }

    LOGIN_SALT: str
    SECRET_KEY: str
    URL_PREFIX: str
    BEHIND_PROXY: bool
    UPLOAD_PATH: str
    TEMP_FILE_PATH: str

    TEMP_FILE_SAVE: bool
    RECV_MAIL_ADDR: str
    SEND_MAIL_ADDR: str
    SEND_MAIL_PASSWD: str
    SEND_MAIL_SMTP_HOST: str
    SEND_MAIL_SMTP_PORT: int
    SEND_MAIL_SMTP_SSL: bool
    MAX_PREVIEW_SIZE: int
    MAX_TEMP_UPLOAD_SIZE: int

    async def _init_database(self):
        db_session = session_maker()

        stmt = select(SystemConfig).where(SystemConfig.key == constants.CONFIG_INIT_KEY)
        result: sqlalchemy.engine.result.ChunkedIteratorResult = await db_session.execute(stmt)
        data = result.scalar()

        if data is None:
            system_config = SystemConfig(key=constants.CONFIG_INIT_KEY, value=json.dumps(True))
            db_session.add(system_config)

            for key, from_env in self._CONFIG_KEYS.items():
                if not from_env:
                    system_config = SystemConfig(key=key, value=json.dumps(self._CONFIG_DEFAULTS[key]))
                    db_session.add(system_config)

        await db_session.commit()
        await db_session.close()
        await engine.dispose()

    async def _load_configs(self):
        db_session = session_maker()

        for key, from_env in self._CONFIG_KEYS.items():
            if from_env:  # 优先从 ENV 中取, 之后取默认值
                value = os.getenv(key)
                if value is None:
                    value = self._CONFIG_DEFAULTS[key]
                _CONFIG_CACHE[key] = value
            else:
                stmt = select(SystemConfig).where(SystemConfig.key == key)
                result: sqlalchemy.engine.result.ChunkedIteratorResult = await db_session.execute(stmt)
                data: SystemConfig = result.scalar()
                _CONFIG_CACHE[key] = json.loads(data.value)

        await db_session.close()
        await engine.dispose()

    def __init__(self):
        asyncio.run(self._init_database())
        asyncio.run(self._load_configs())

    def __setattr__(self, key, value):
        if key in self._CONFIG_KEYS and self._CONFIG_KEYS[key]:
            _CONFIG_CACHE[key] = value

            async def _update_database():
                db_session = session_maker()

                result = await db_session.execute(select(SystemConfig).where(SystemConfig.key == key))
                system_config = result.scalar()
                system_config.value = json.dumps(value)
                db_session.add(system_config)

                await db_session.commit()
                await db_session.close()
            asyncio.create_task(_update_database())
        else:
            raise Exception(f'Config key {key} not existed or not mutable')

    def __getattr__(self, key):
        if key in self._CONFIG_KEYS:
            return _CONFIG_CACHE[key]
        else:
            raise Exception(f'Config key {key} not existed')
