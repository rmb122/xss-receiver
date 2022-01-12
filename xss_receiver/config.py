import asyncio
import json
import multiprocessing
import os
import typing

import sqlalchemy
from sqlalchemy import func
from sqlalchemy.future import select

from xss_receiver import constants
from xss_receiver.database import session_maker, engine
from xss_receiver.models import SystemConfig, User
from xss_receiver.utils import passwd_hash

_manager = multiprocessing.Manager()
_CONFIG_CACHE = _manager.dict()


class Config:
    # name: [from_env, public, mutable, default_value, comment]
    _CONFIG_KEYS: typing.Dict[str, typing.Tuple[bool, bool, bool, typing.Any, str]] = {
        'SECRET_KEY': [True, False, False, os.urandom(32), ''],
        'URL_PREFIX': [True, False, False, '', ''],
        'BEHIND_PROXY': [True, False, False, False, ''],
        'UPLOAD_PATH': [True, False, False, '/tmp', ''],
        'TEMP_FILE_PATH': [True, False, False, '/tmp', ''],

        'PASSWORD_SALT': [False, False, False, os.urandom(32).hex(), ''],
        'TEMP_FILE_SAVE': [False, True, True, False, '是否保存临时文件'],
        'RECV_MAIL_ADDR': [False, True, True, '', '收件地址'],
        'SEND_MAIL_ADDR': [False, True, True, '', '发件地址'],
        'SEND_MAIL_PASSWD': [False, True, True, '', '发件邮箱密码'],
        'SEND_MAIL_SMTP_HOST': [False, True, True, '', 'SMTP 服务器地址'],
        'SEND_MAIL_SMTP_PORT': [False, True, True, 465, 'SMTP 服务器端口'],
        'SEND_MAIL_SMTP_SSL': [False, True, True, True, 'SMTP 是否启用 SSL'],
        'MAX_PREVIEW_SIZE': [False, True, True, 1048576, '最大预览大小'],
        'MAX_TEMP_UPLOAD_SIZE': [False, True, True, 1048576, '最大临时文件上传大小']
    }

    PASSWORD_SALT: str
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

    async def _init_config_table(self):
        db_session = session_maker()

        stmt = select(SystemConfig).where(SystemConfig.key == constants.CONFIG_INIT_KEY)
        result: sqlalchemy.engine.result.ChunkedIteratorResult = await db_session.execute(stmt)
        data = result.scalar()

        if data is None:
            system_config = SystemConfig(key=constants.CONFIG_INIT_KEY, value=True)
            db_session.add(system_config)

            for key, settings in self._CONFIG_KEYS.items():
                if not settings[0]:
                    system_config = SystemConfig(key=key, value=self._CONFIG_KEYS[key][3])
                    db_session.add(system_config)

        await db_session.commit()
        await db_session.close()
        await engine.dispose()

    async def _init_admin(self):
        db_session = session_maker()
        count = (await db_session.execute(select(func.count('1')).select_from(User))).scalar()

        if count == 0:
            user = User(username='admin', password=passwd_hash(passwd_hash('admin', 'admin'), self.PASSWORD_SALT), user_type=constants.USER_TYPE_SUPER_ADMIN)
            db_session.add(user)
            await db_session.commit()

        await db_session.close()
        await engine.dispose()

    async def _load_configs(self):
        db_session = session_maker()

        for key, settings in self._CONFIG_KEYS.items():
            if settings[0]:  # 优先从 ENV 中取, 之后取默认值
                value = os.getenv(key)
                if value is None:
                    value = self._CONFIG_KEYS[key][3]
                else:
                    value = json.loads(value)
                _CONFIG_CACHE[key] = value
            else:
                stmt = select(SystemConfig).where(SystemConfig.key == key)
                result: sqlalchemy.engine.result.ChunkedIteratorResult = await db_session.execute(stmt)
                data: SystemConfig = result.scalar()
                _CONFIG_CACHE[key] = data.value

        await db_session.close()
        await engine.dispose()

    def __init__(self):
        asyncio.run(self._init_config_table())
        asyncio.run(self._load_configs())
        asyncio.run(self._init_admin())

    def __setattr__(self, key, value):
        if key in self._CONFIG_KEYS and self._CONFIG_KEYS[key][2]:
            _CONFIG_CACHE[key] = value

            async def _update_database():
                db_session = session_maker()

                result = await db_session.execute(select(SystemConfig).where(SystemConfig.key == key))
                system_config = result.scalar()
                system_config.value = value
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

    def get_public_config(self):
        configs = {}
        for key, settings in self._CONFIG_KEYS.items():
            if settings[1]:
                configs[key] = _CONFIG_CACHE[key]
        return configs

    def get_config_privileges(self, key):
        if key in self._CONFIG_KEYS:
            return self._CONFIG_KEYS[key][1:3]
        else:
            return False, False

    def get_config_type(self, key):
        return type(self._CONFIG_KEYS[key][3])

    def get_config_comment(self, key):
        return self._CONFIG_KEYS[key][4]
