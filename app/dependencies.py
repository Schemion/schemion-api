from app.config import settings
from app.database import SessionLocal
from app.infrastructure.cloud_storage.minio_storage import MinioStorage


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_storage():
    storage = MinioStorage(
        endpoint=settings.MINIO_ENDPOINT,
        public_endpoint = settings.MINIO_PUBLIC_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        bucket=settings.MINIO_BUCKET
    )
    return storage