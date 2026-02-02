from dishka import make_async_container

from app.infrastructure.di.service_provider import ServiceProvider
from app.infrastructure.di.sqlalchemy_provider import SQLAlchemyProvider

container = make_async_container(SQLAlchemyProvider(), ServiceProvider())
