from app.config import settings
from app.database import AsyncSessionLocal
from app.infrastructure.services.cache.cache_service import CacheService
from app.infrastructure.services.cloud_storage.minio_storage import MinioStorage


async def get_db():
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()


def get_storage():
    storage = MinioStorage(
        endpoint=settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
    )
    return storage

def get_redis():
    return CacheService(settings.REDIS_URL)