import pytest_asyncio

from app.db.connection import connect_to_database, disconnect_from_database


@pytest_asyncio.fixture(scope="session", autouse=True)
async def database_pool():
    await connect_to_database()
    yield
    await disconnect_from_database()
