from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    REDIS_URL: str = "redis://:adminpass@redis:6379/0"
    DATABASE_URL: str = "postgresql+asyncpg://admin:admin@database:5432/schemion"
    RABBITMQ_URL: str = "amqp://admin:admin@rabbitmq:5672/"
    JWT_SECRET: str = "supersecret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_PUBLIC_ENDPOINT: str = "files.localhost"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SCHEMAS_BUCKET: str = "schemas-images"
    MINIO_MODELS_BUCKET: str = "models"
    MINIO_DATASETS_BUCKET: str = "datasets"

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_ignore_empty=True
    )


settings = Settings()
