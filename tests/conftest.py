from hmac import compare_digest
from unittest import mock

import pytest
from beanie import init_beanie
from httpx import AsyncClient
from mongomock_motor import AsyncMongoMockClient
from slugify import slugify
from starlette import status

from src.common.helpers.error_codes import AppErrorCode
from src.common.helpers.exception import CustomHTTPException
from src.config import settings
from src.shared import CHECK_ACCESS_ALLOW_ENDPOINT, CHECK_VALIDATE_ACCESS_TOKEN_ENDPOINT


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
def mock_check_assess_allow():
    async def mock_check_access(authorization: str, url: str = CHECK_ACCESS_ALLOW_ENDPOINT):
        if authorization == "fake_token":
            return True
        else:
            return False

    with mock.patch("src.endpoint.CheckAccessAllow.__call__", new_callable=mock.AsyncMock) as mock_call:
        mock_call.side_effect = mock_check_access
        yield mock_call


@pytest.fixture(autouse=True)
def mock_verify_assess_token(fake_data):
    async def _mock_verify_access(authorization: str, url: str = CHECK_VALIDATE_ACCESS_TOKEN_ENDPOINT):
        # Simuler le comportement de séparation du token comme dans la classe originale
        token = authorization.split()[1] if authorization else None

        # Vérifier les cas d'erreur comme dans la classe originale
        if not token or token in ["null", "undefined"]:
            raise CustomHTTPException(
                code_error=AppErrorCode.AUTH_ACCESS_DENIED,
                message_error="Access denied",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        # Simuler le comportement pour un token valide
        if compare_digest(token, "fake_token"):
            return {
                "active": True,
                "user_info": {
                    "_id": fake_data.uuid4(),
                    "user_id": fake_data.uuid4(),
                    "role": {"name": settings.ROLE_SUPER_ADMIN, "slug": slugify(settings.ROLE_SUPER_ADMIN)},
                },
            }

        # Simuler un token invalide
        return {"active": False, "user_info": None}

    with mock.patch("src.endpoint.VerifyAccessToken.__call__", new_callable=mock.AsyncMock) as mock_call:
        mock_call.side_effect = _mock_verify_access
        yield mock_call


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
