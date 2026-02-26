import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.storage.memory_store import InMemorySessionStore
from app import dependencies


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def store():
    return InMemorySessionStore()
