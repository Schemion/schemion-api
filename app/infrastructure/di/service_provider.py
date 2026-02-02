from dishka import Provider, Scope, provide

from app.config import settings
from app.core.interfaces import ICacheRepository, IDatasetRepository, IModelRepository, IStorageRepository, \
    ITaskRepository, IUserRepository
from app.core.services import DatasetService, ModelService, TaskService, UserService
from app.core.services.auth_service import AuthService
from app.infrastructure.services.cache import CacheService
from app.infrastructure.services.cloud_storage import MinioStorage


class ServiceProvider(Provider):
    @provide(scope=Scope.APP)
    def minio_storage(self) -> MinioStorage:
        return MinioStorage(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            bucket=settings.MINIO_SCHEMAS_BUCKET,
        )

    @provide(scope=Scope.APP)
    def cache_service(self) -> CacheService:
        return CacheService(url=settings.REDIS_URL)

    @provide(scope=Scope.REQUEST)
    def get_user_service(self, user_repository: IUserRepository, cache_repository: CacheService) -> UserService:
        return UserService(user_repository, cache_repository)

    @provide(scope=Scope.REQUEST)
    def get_auth_service(self, user_repository: IUserRepository) -> AuthService:
        return AuthService(user_repository)

    @provide(scope=Scope.REQUEST)
    def get_task_service(self, task_repository: ITaskRepository, model_repository: IModelRepository,
                         dataset_repository: IDatasetRepository, storage_repository: MinioStorage,
                         cache_repository: CacheService) -> TaskService:
        return TaskService(task_repo=task_repository, storage=storage_repository, model_repo=model_repository,
                           dataset_repo=dataset_repository, cache_repo=cache_repository)

    @provide(scope=Scope.REQUEST)
    def get_dataset_service(self, dataset_repository: IDatasetRepository, cache_repository: CacheService,
                            storage_repository: MinioStorage) -> DatasetService:
        return DatasetService(dataset_repo=dataset_repository, cache_repo=cache_repository, storage=storage_repository)

    @provide(scope=Scope.REQUEST)
    def get_model_service(self, model_repository: IModelRepository, dataset_repository: IDatasetRepository,
                          cache_repository: CacheService, storage_repository: MinioStorage) -> ModelService:
        return ModelService(model_repo=model_repository, cache_repo=cache_repository, storage=storage_repository,
                            dataset_repo=dataset_repository)
