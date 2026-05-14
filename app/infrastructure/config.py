from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://admin:admin@database:5432/schemion"
    JWT_SECRET: str = "supersecret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_PUBLIC_ENDPOINT: str = "files.localhost"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SCHEMAS_BUCKET: str = "schemas-images"
    MINIO_MODELS_BUCKET: str = "models"
    MINIO_DATASETS_BUCKET: str = "datasets"
    MINIO_METRICS_BUCKET: str = "metrics"
    MINIO_INFERENCES_BUCKET: str = "inference-results"
    BOBBER_HOST: str = "bob-the-broker"
    BOBBER_PORT: int = 50051
    MAIL_SMTP_HOST: str = "schemion-mail"
    MAIL_SMTP_PORT: int = 1025
    MAIL_SMTP_TIMEOUT_SECONDS: int = 10
    MAIL_FROM: str = "no-reply@schemion.local"
    REGISTRATION_CODE_TTL_SECONDS: int = 10 * 60
    REGISTRATION_CODE_LENGTH: int = 6
    REGISTRATION_CODE_MAX_ATTEMPTS: int = 5

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_ignore_empty=True
    )


settings = Settings()
