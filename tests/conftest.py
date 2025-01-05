import pytest
import pytest_asyncio
from beanie import init_beanie
from httpx import AsyncClient
from mongomock_motor import AsyncMongoMockClient

from src.config import settings


@pytest.fixture()
def fake_data():
    import faker

    return faker.Faker()


@pytest.fixture()
def fixture_models():
    from src import models

    return models


@pytest.fixture
async def mock_app_instance():
    from src.main import app as mock_app

    yield mock_app


@pytest.fixture(autouse=True)
async def mock_mongodb_client(mock_app_instance, fixture_models):
    client = AsyncMongoMockClient()
    mock_app_instance.mongo_db_client = client[settings.MONGO_DB]
    await init_beanie(
        database=mock_app_instance.mongo_db_client,
        document_models=fixture_models.document_models,
    )
    yield client


@pytest.fixture(autouse=True)
async def clean_db(fixture_models, mock_mongodb_client):
    models = fixture_models.document_models
    yield None

    for model in models:
        await model.delete_all()
        await model.get_motor_collection().drop()
        await model.get_motor_collection().drop_indexes()


@pytest.fixture(autouse=True)
async def http_client_api(mock_app_instance, clean_db):
    """api client fixture."""
    async with AsyncClient(app=mock_app_instance, base_url="http://apikeys.localhost.io") as ac:
        yield ac


@pytest.fixture()
def fake_api_data(fake_data):
    return {"user_id": fake_data.uuid4()}


@pytest_asyncio.fixture()
async def create_apikey(fixture_models, fake_api_data):
    result = await fixture_models.APIKeyDocument(**fake_api_data).create()
    return result
