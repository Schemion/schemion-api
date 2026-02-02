from contextlib import asynccontextmanager

from app.infrastructure.database import AsyncSessionLocal


# TODO: По возможности избавиться от это файла в целом

async def get_db():
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()


@asynccontextmanager
async def get_db_session():
    async for db in get_db():
        yield db
