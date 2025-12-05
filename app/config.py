import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://:adminpass@redis:6379/0")
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "adminpass")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://admin:admin@database:5432/schemion")
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://admin:admin@rabbitmq:5672/")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "supersecret")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 10))
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    MINIO_PUBLIC_ENDPOINT: str = os.getenv("MINIO_PUBLIC_ENDPOINT", "files.localhost")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_SCHEMAS_BUCKET: str = os.getenv("MINIO_SCHEMAS_BUCKET", "schemas-images")
    MINIO_MODELS_BUCKET: str = os.getenv("MINIO_MODELS_BUCKET", "models")
    MINIO_DATASETS_BUCKET: str = os.getenv("MINIO_DATASETS_BUCKET", "datasets")

settings = Settings()