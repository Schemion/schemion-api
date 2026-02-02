from typing import AsyncIterator

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.interfaces import IDatasetRepository, IModelRepository, ITaskRepository, IUserRepository
from app.database import AsyncSessionLocal
from app.infrastructure.database.repositories import DatasetRepository, ModelRepository, TaskRepository, UserRepository


class SQLAlchemyProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def get_session(self) -> AsyncIterator[AsyncSession]:
        async with AsyncSessionLocal() as session:
            yield session

    @provide(scope=Scope.REQUEST)
    def get_user_repository(self, session: AsyncSession) -> IUserRepository:
        return UserRepository(session)

    @provide(scope=Scope.REQUEST)
    def get_task_repository(self, session: AsyncSession) -> ITaskRepository:
        return TaskRepository(session)

    @provide(scope=Scope.REQUEST)
    def get_model_repository(self, session: AsyncSession) -> IModelRepository:
        return ModelRepository(session)

    @provide(scope=Scope.REQUEST)
    def get_dataset_repository(self, session: AsyncSession) -> IDatasetRepository:
        return DatasetRepository(session)
