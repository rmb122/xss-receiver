import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

from xss_receiver import models

engine = create_async_engine("mysql+aiomysql://root:root@172.17.0.2/xss")
session_maker = sessionmaker(engine, AsyncSession, expire_on_commit=False)


async def _init_database():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    await engine.dispose()


asyncio.run(_init_database())
