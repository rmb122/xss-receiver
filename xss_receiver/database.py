import asyncio

import sanic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

from xss_receiver import models

engine = create_async_engine("mysql+aiomysql://root:root@172.17.0.2/xss")
session_maker = sessionmaker(engine, AsyncSession, expire_on_commit=False)


async def _init_database():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    # asyncio.run 每次都会新建一个 loop, 而 sqlalchemy 会有连接池, 需要 dispose, 不然下一次 run 的 loop 不同, 连接池会炸掉
    await engine.dispose()


def inject_database_session(app: sanic.Sanic):
    @app.middleware("request")
    async def inject_session(request):
        request.ctx.db_session = session_maker()

    @app.middleware("response")
    async def close_session(request, response):
        if hasattr(request.ctx, "db_session"):
            await request.ctx.db_session.close()


asyncio.run(_init_database())
