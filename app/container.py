from dependency_injector import containers, providers
from app.config import settings
from app.infrastructure.services.cloud_storage.minio_storage import MinioStorage
from app.infrastructure.services.cache.cache_service import CacheService
from app.infrastructure.database.repositories import ModelRepository, DatasetRepository, UserRepository, TaskRepository
from app.core.services import ModelService, DatasetService, UserService, TaskService


class ApplicationContainer(containers.DeclarativeContainer):

    wiring_config = containers.WiringConfiguration(
        packages=[
            "app.presentation.routers",
            "app.common.admin",
            "app.common.security"
        ]
    )

    config = providers.Configuration()

    # Синглетончесы
    storage = providers.Singleton(
        MinioStorage,
        endpoint=settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY
    )

    cache = providers.Singleton(
        CacheService,
        url=settings.REDIS_URL
    )

    # Не помню как называется, но создаются каждый раз
    # репосы
    model_repository = providers.Factory(
        ModelRepository,
    )

    dataset_repository = providers.Factory(
        DatasetRepository,
    )

    user_repository = providers.Factory(
        UserRepository,
    )

    task_repository = providers.Factory(
        TaskRepository,
    )

    # сервисы
    model_service = providers.Factory(
        ModelService,
        model_repo=model_repository,
        storage=storage,
        dataset_repo=dataset_repository,
        cache_repo=cache
    )

    task_service = providers.Factory(
        TaskService,
        task_repo=task_repository,
        storage=storage,
        model_repo=model_repository,
        dataset_repo=dataset_repository,
        cache_repo=cache
    )

    user_service = providers.Factory(
        UserService,
        user_repo=user_repository,
        cache_repo=cache
    )

    dataset_service = providers.Factory(
        DatasetService,
        dataset_repo=dataset_repository,
        storage=storage,
        cache_repo=cache
    )


