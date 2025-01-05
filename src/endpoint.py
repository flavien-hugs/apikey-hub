from datetime import datetime, timezone
from typing import Literal, Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, status
from fastapi_pagination.ext.beanie import paginate
from pymongo import DESCENDING, ASCENDING

from src.common.helpers.pagination import customize_page
from src.common.helpers.utils import SortEnum
from src.models import APIKeyBaseSchema, APIKeyDocument, APIKeyFilterSchema
from src.shared import find_document, generate_api_key, parse_api_key, verify_api_key

router = APIRouter(prefix="/keys", tags=["API KEYS"])


@router.post(
    "",
    response_model=APIKeyDocument,
    response_model_by_alias=True,
    response_model_exclude={"hashed_key"},
    summary="Create new API Key (Soft Create)",
    status_code=status.HTTP_201_CREATED,
)
async def create(payload: APIKeyBaseSchema = Body(...)):
    raw_api_key, hashed_key = generate_api_key(payload.user_id)
    new_doc = await APIKeyDocument(**payload.model_dump(), api_key=raw_api_key, hashed_key=hashed_key).create()
    return new_doc


@router.get(
    "",
    response_model=customize_page(APIKeyDocument),
    response_model_by_alias=True,
    response_model_exclude={"hashed_key"},
    summary="Get all API Keys (Soft Read)",
    status_code=status.HTTP_200_OK,
)
async def all(
    query: APIKeyFilterSchema = Depends(APIKeyFilterSchema),
    sort: Optional[SortEnum] = Query(default=SortEnum.DESC, description="Sort order"),
):
    search = query.model_dump(exclude_none=True)

    if query.user_id:
        search["user_id"] = query.user_id
    if query.is_active:
        search["is_active"] = query.is_active
    if query.last_used_at:
        search["last_used_at"] = query.last_used_at
    if query.expires_at:
        search["expires_at"] = query.expires_at
    if query.created_at:
        search["created_at"] = query.created_at

    sort_ = DESCENDING if sort == SortEnum.DESC else ASCENDING
    apikeys_docs = APIKeyDocument.find(search, sort=[("created_at", sort_)])
    return await paginate(apikeys_docs)


@router.get(
    "/{id}",
    response_model=APIKeyDocument,
    response_model_by_alias=True,
    response_model_exclude={"hashed_key"},
    summary="Get API Key by ID (Soft Read)",
    status_code=status.HTTP_200_OK,
)
async def read(id: PydanticObjectId):
    return await find_document(document=APIKeyDocument, query={"_id": id}, status_code=status.HTTP_404_NOT_FOUND)


@router.put(
    "/{id}",
    response_model=APIKeyDocument,
    response_model_by_alias=True,
    response_model_exclude={"hashed_key"},
    summary="Regenerate API Key by ID (Soft Update)",
    status_code=status.HTTP_202_ACCEPTED,
)
async def regenerate_apikey(id: PydanticObjectId):
    doc = await find_document(document=APIKeyDocument, query={"_id": id}, status_code=status.HTTP_400_BAD_REQUEST)
    return await doc.regenerate_api_key(id=id, user_id=doc.user_id)


@router.put(
    "/{id}/action",
    response_model=APIKeyDocument,
    response_model_by_alias=True,
    response_model_exclude={"hashed_key"},
    summary="Activate or deactivate API Key by ID (Soft Update)",
    status_code=status.HTTP_202_ACCEPTED,
)
async def activate_or_deactivate_apikey(id: PydanticObjectId, action: Literal["activate", "deactivate"]):
    doc = await find_document(document=APIKeyDocument, query={"_id": id}, status_code=status.HTTP_400_BAD_REQUEST)
    is_active = True if action == "activate" else False
    return await doc.set({"is_active": is_active, "updated_at": datetime.now(timezone.utc)})


@router.delete(
    "/{id}",
    summary="Delete API Key by ID (Soft Delete)",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove(id: PydanticObjectId):
    await APIKeyDocument.find_one({"_id": id}).delete()


router.prefix = ""
router.tags = ["VERIFY API KEYS"]


@router.get(
    "/verify-api-key",
    summary="Verify API Key (Soft Read)",
    status_code=status.HTTP_200_OK,
)
async def verify_apikey(apikey: str = Header(..., description="API Key to verify", alias="X-API-Key")):
    try:
        # Valider format et extraire user_id
        is_valid, _, user_id = parse_api_key(apikey)
        if not is_valid:
            return {"verified": False}

        # Vérifier existence du document
        if (doc := await APIKeyDocument.find_one({"user_id": user_id})) is None:
            return {"verified": False}

        # Vérifier la clé fournie
        is_valid, extracted_user_id = verify_api_key(apikey, doc.hashed_key)

        result = {"verified": is_valid and str(doc.user_id) == str(extracted_user_id)}

    except HTTPException:
        return {"verified": False}

    return result
