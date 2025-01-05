import pytest
from starlette import status


@pytest.mark.asyncio
async def test_ping_api(http_client_api):
    response = await http_client_api.get("/apikeys/@ping")
    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json() == {"message": "pong !"}


@pytest.mark.asyncio
async def test_create_api_keys_success_uses_cases(http_client_api, fake_api_data):
    # CASE 1: Create API Key with valid user_id
    case_one_resp = await http_client_api.post("/keys", json=fake_api_data)
    assert case_one_resp.status_code == status.HTTP_201_CREATED, case_one_resp.text
    assert case_one_resp.json()["user_id"] == fake_api_data["user_id"]
    assert "hashed_key" not in case_one_resp.json()

    # CASE 3: Create API Key with missing user_id
    case_three_resp = await http_client_api.post("/keys", json={})
    assert case_three_resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, case_three_resp.text
    assert case_three_resp.json()["code_error"] == "app/unprocessable-entity"


@pytest.mark.asyncio
@pytest.mark.parametrize("sort", ["asc", "desc"])
@pytest.mark.parametrize("is_active", [True, False])
async def test_read_all_uses_cases(http_client_api, fake_api_data, fake_data, sort, is_active):
    create_apikey_resp = await http_client_api.post("/keys", json=fake_api_data)
    assert create_apikey_resp.status_code == status.HTTP_201_CREATED, create_apikey_resp.text

    response = create_apikey_resp.json()
    assert response.get("user_id") == fake_api_data["user_id"]

    # CASE 1: Search without params
    all_resp = await http_client_api.get("/keys")
    assert all_resp.status_code == status.HTTP_200_OK, all_resp.text
    assert all_resp.json().get("total") >= 1

    # CASE 2: Search with sort
    sort_resp = await http_client_api.get("/keys", params={"sort": sort})
    assert sort_resp.status_code == status.HTTP_200_OK, sort_resp.text
    assert sort_resp.json().get("total") >= 1

    # CASE 3: Search with 'user_id' param
    user_resp = await http_client_api.get("/keys", params={"user_id": response["user_id"]})
    assert user_resp.status_code == status.HTTP_200_OK, user_resp.text

    result = user_resp.json()
    assert result.get("total") >= 1
    assert result.get("items")[0]["user_id"] == fake_api_data["user_id"]

    # CASE 4: Search with invalid 'user_id' param
    invalid_user_resp = await http_client_api.get("/keys", params={"user_id": fake_data.uuid4()})
    assert invalid_user_resp.status_code == status.HTTP_200_OK, invalid_user_resp.text
    assert invalid_user_resp.json().get("total") == 0

    # CASE 5: Search with 'is_active' param
    active_resp = await http_client_api.get("/keys", params={"is_active": is_active})
    assert active_resp.status_code == status.HTTP_200_OK, active_resp.text
    assert active_resp.json().get("total") >= 1 if is_active else active_resp.json().get("total") == 0

    # CASE 6: Search with 'last_used_at' param
    last_used_at = fake_data.date_time_this_month()
    last_used_at_resp = await http_client_api.get("/keys", params={"last_used_at": last_used_at})
    assert last_used_at_resp.status_code == status.HTTP_200_OK, last_used_at_resp.text
    assert last_used_at_resp.json().get("total") == 0

    # CASE 7: Search with 'expires_at' param
    expires_at = fake_data.date_time_this_month()
    expires_at_resp = await http_client_api.get("/keys", params={"expires_at": expires_at})
    assert expires_at_resp.status_code == status.HTTP_200_OK, expires_at_resp.text
    assert expires_at_resp.json().get("total") == 0

    # CASE 8: Search with 'created_at' param
    created_at = fake_data.date_time_this_month()
    created_at_resp = await http_client_api.get("/keys", params={"created_at": created_at})
    assert created_at_resp.status_code == status.HTTP_200_OK, created_at_resp.text
    assert created_at_resp.json().get("total") == 0


@pytest.mark.asyncio
async def test_read_one_uses_cases(http_client_api, fake_api_data):
    create_apikey_resp = await http_client_api.post("/keys", json=fake_api_data)
    assert create_apikey_resp.status_code == status.HTTP_201_CREATED, create_apikey_resp.text

    response = create_apikey_resp.json()

    # CASE 1: Read API Key by ID
    read_resp = await http_client_api.get(f"/keys/{response['_id']}")
    assert read_resp.status_code == status.HTTP_200_OK, read_resp.text
    assert read_resp.json()["_id"] == response["_id"]
    assert read_resp.json()["user_id"] == response["user_id"]
    assert "hashed_key" not in read_resp.json()

    # CASE 2: Read API Key by invalid ID
    invalid_id_resp = await http_client_api.get("/keys/invalid-id")
    assert invalid_id_resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, invalid_id_resp.text
    assert invalid_id_resp.json()["code_error"] == "app/unprocessable-entity"

    # CASE 3: Read API Key by non-existent ID
    non_existent_id_resp = await http_client_api.get("/keys/66f6fd2f9efb2cbc83fbb133")
    assert non_existent_id_resp.status_code == status.HTTP_404_NOT_FOUND, non_existent_id_resp.text
    assert non_existent_id_resp.json()["code_error"] == "document/document-not-found"
    assert non_existent_id_resp.json()["message_error"] == "Document not found"


@pytest.mark.asyncio
async def test_regenerate_apikey_uses_cases(http_client_api, fake_api_data):
    create_apikey_resp = await http_client_api.post("/keys", json=fake_api_data)
    assert create_apikey_resp.status_code == status.HTTP_201_CREATED, create_apikey_resp.text

    response = create_apikey_resp.json()

    # CASE 1: Regenerate API Key by ID
    regenerate_resp = await http_client_api.put(f"/keys/{response['_id']}")
    assert regenerate_resp.status_code == status.HTTP_202_ACCEPTED, regenerate_resp.text
    assert regenerate_resp.json()["_id"] == response["_id"]
    assert regenerate_resp.json()["user_id"] == response["user_id"]
    assert "hashed_key" not in regenerate_resp.json()
    assert regenerate_resp.json()["api_key"] != response["api_key"]

    # CASE 2: Regenerate API Key by invalid ID
    invalid_id_resp = await http_client_api.put("/keys/invalid-id")
    assert invalid_id_resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, invalid_id_resp.text
    assert invalid_id_resp.json()["code_error"] == "app/unprocessable-entity"

    # CASE 3: Regenerate API Key by non-existent ID
    non_existent_id_resp = await http_client_api.put("/keys/66f6fd2f9efb2cbc83fbb133")
    assert non_existent_id_resp.status_code == status.HTTP_400_BAD_REQUEST, non_existent_id_resp.text
    assert non_existent_id_resp.json()["code_error"] == "document/document-not-found"
    assert non_existent_id_resp.json()["message_error"] == "Document not found"


@pytest.mark.asyncio
@pytest.mark.parametrize("action", ["activate", "deactivate"])
async def test_activate_or_deactivate_apikey_uses_cases(http_client_api, fake_api_data, action):
    create_apikey_resp = await http_client_api.post("/keys", json=fake_api_data)
    assert create_apikey_resp.status_code == status.HTTP_201_CREATED, create_apikey_resp.text

    response = create_apikey_resp.json()

    # CASE 1: Update API Key by ID
    update_resp = await http_client_api.put(f"/keys/{response['_id']}/action", params={"action": action})
    assert update_resp.status_code == status.HTTP_202_ACCEPTED, update_resp.text
    assert update_resp.json()["_id"] == response["_id"]
    assert update_resp.json()["is_active"] == (True if action == "activate" else False)

    # CASE 2: Update API Key by invalid ID
    invalid_id_resp = await http_client_api.put("/keys/invalid-id/action", params={"action": action})
    assert invalid_id_resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, invalid_id_resp.text
    assert invalid_id_resp.json()["code_error"] == "app/unprocessable-entity"

    # CASE 3: Update API Key by non-existent ID
    non_existent_id_resp = await http_client_api.put("/keys/66f6fd2f9efb2cbc83fbb133/action", params={"action": action})
    assert non_existent_id_resp.status_code == status.HTTP_400_BAD_REQUEST, non_existent_id_resp.text
    assert non_existent_id_resp.json()["code_error"] == "document/document-not-found"
    assert non_existent_id_resp.json()["message_error"] == "Document not found"

    # CASE 4: Update API Key by invalid action
    invalid_action_resp = await http_client_api.put(f"/keys/{response['_id']}/action", params={"action": "invalid-action"})
    assert invalid_action_resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, invalid_action_resp.text
    assert invalid_action_resp.json()["code_error"] == "app/unprocessable-entity"


@pytest.mark.asyncio
async def test_remove_apikey_uses_cases(http_client_api, fake_api_data):
    create_apikey_resp = await http_client_api.post("/keys", json=fake_api_data)
    assert create_apikey_resp.status_code == status.HTTP_201_CREATED, create_apikey_resp.text

    response = create_apikey_resp.json()

    # CASE 1: Delete API Key by ID
    delete_resp = await http_client_api.delete(f"/keys/{response['_id']}")
    assert delete_resp.status_code == status.HTTP_204_NO_CONTENT, delete_resp.text

    # CASE 2: Delete API Key by invalid ID
    invalid_id_resp = await http_client_api.delete("/keys/invalid-id")
    assert invalid_id_resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, invalid_id_resp.text
    assert invalid_id_resp.json()["code_error"] == "app/unprocessable-entity"

    # CASE 3: Delete API Key by non-existent ID
    non_existent_id_resp = await http_client_api.delete("/keys/66f6fd2f9efb2cbc83fbb133")
    assert non_existent_id_resp.status_code == status.HTTP_204_NO_CONTENT, non_existent_id_resp.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "headers, expected_status, expected_verified",
    [
        # CASE 1: Clé API valide
        ({"X-API-Key": True}, status.HTTP_200_OK, True),
        ({"X-API-Key": "valid-key"}, status.HTTP_200_OK, False),
        ({}, status.HTTP_422_UNPROCESSABLE_ENTITY, None),
    ],
)
async def test_verify_api_key_uses_cases(
    http_client_api, fake_api_data, headers: dict, expected_status: int, expected_verified: bool | None
):
    # GIVEN: Créer une clé API
    create_apikey_resp = await http_client_api.post("/keys", json=fake_api_data)
    assert create_apikey_resp.status_code == status.HTTP_201_CREATED, create_apikey_resp.text

    # Remplacer True par la vraie clé API dans les headers si nécessaire
    if headers.get("X-API-Key") is True:
        headers["X-API-Key"] = create_apikey_resp.json()["api_key"]

    # WHEN: Vérifier la clé API fournie dans les headers de la requête
    verify_response = await http_client_api.get("/verify-api-key", headers=headers)

    # THEN: Vérifier la réponse de la requête en fonction des cas d'utilisation
    assert verify_response.status_code == expected_status, verify_response.text

    if expected_verified is not None:
        print(verify_response.json())

        assert verify_response.json()["verified"] == expected_verified, verify_response.text
