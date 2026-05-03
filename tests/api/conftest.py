import pytest

from app.infrastructure.database import engine


@pytest.fixture(autouse=True)
async def dispose_engine_between_tests():
    yield
    await engine.dispose()
