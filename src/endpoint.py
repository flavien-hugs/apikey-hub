from datetime import datetime, timezone
from typing import Literal, Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query, Request, status
from fastapi_pagination.ext.beanie import paginate
from pymongo import ASCENDING, DESCENDING
from slugify import slugify

from src.common.depends.permission import VerifyAccessToken, CheckAccessAllow
from src.common.helpers.exception import CustomHTTPException
from src.common.helpers.pagination import customize_page
from src.common.helpers.utils import SortEnum
from src.common.services.trailhub_client import send_event
from src.config import settings
from src.models import APIKeyDocument, APIKeyFilterSchema
from src.shared import (
    API_TRAILHUB_ENDPOINT,
    APIKeyErrorCode,
    CHECK_ACCESS_ALLOW_ENDPOINT,
    CHECK_VALIDATE_ACCESS_TOKEN_ENDPOINT,
    find_document,
    generate_api_key,
    parse_api_key,
    verify_api_key,
)

router = APIRouter(prefix="/keys", tags=["API KEYS"])


@router.post(
    "",
    dependencies=[
        Depends(CheckAccessAllow(url=CHECK_ACCESS_ALLOW_ENDPOINT, permissions={"apikey:can-make-apikey"})),
    ],
    response_model=APIKeyDocument,
    response_model_by_alias=True,
    response_model_exclude={"hashed_key"},
    summary="Create new API Key (Soft Create)",
    status_code=status.HTTP_201_CREATED,
)
async def create(
    request: Request,
    background: BackgroundTasks,
    token_info: dict = Depends(VerifyAccessToken(url=CHECK_VALIDATE_ACCESS_TOKEN_ENDPOINT)),
):
    user_id = token_info.get("user_info", {}).get("_id")

    raw_api_key, hashed_key = generate_api_key(user_id)
    new_doc = await APIKeyDocument(user_id=user_id, api_key=raw_api_key, hashed_key=hashed_key).create()

    if settings.USE_TRACK_ACTIVITY_LOGS:
        await send_event(
            request=request,
            bg=background,
            oauth_url=CHECK_VALIDATE_ACCESS_TOKEN_ENDPOINT,
            trailhub_url=API_TRAILHUB_ENDPOINT,
            source=settings.APP_NAME.lower(),
            message="has created new api key",
            user_id=str(user_id),
        )

    return new_doc


@router.get(
    "",
    dependencies=[
        Depends(CheckAccessAllow(url=CHECK_ACCESS_ALLOW_ENDPOINT, permissions={"apikey:can-read-apikey"})),
    ],
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
    dependencies=[
        Depends(CheckAccessAllow(url=CHECK_ACCESS_ALLOW_ENDPOINT, permissions={"apikey:can-read-apikey"})),
    ],
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
    dependencies=[
        Depends(CheckAccessAllow(url=CHECK_ACCESS_ALLOW_ENDPOINT, permissions={"apikey:can-regenerate-apikey"})),
    ],
    response_model=APIKeyDocument,
    response_model_by_alias=True,
    response_model_exclude={"hashed_key"},
    summary="Regenerate API Key by ID (Soft Update)",
    status_code=status.HTTP_202_ACCEPTED,
)
async def regenerate_apikey(
    request: Request,
    background: BackgroundTasks,
    id: PydanticObjectId,
    token_info: dict = Depends(VerifyAccessToken(url=CHECK_VALIDATE_ACCESS_TOKEN_ENDPOINT)),
):
    doc = await find_document(document=APIKeyDocument, query={"_id": id}, status_code=status.HTTP_400_BAD_REQUEST)

    user_info = token_info.get("user_info", {})
    user_id = user_info.get("_id")
    if user_id != str(doc.user_id) and not user_info.get("role", {}).get("slug") != slugify(settings.ROLE_SUPER_ADMIN):
        raise CustomHTTPException(
            code_error=APIKeyErrorCode.CANNOT_ACCESS_RESOURCE,
            message_error="You cannot access this resource",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    if settings.USE_TRACK_ACTIVITY_LOGS:
        await send_event(
            request=request,
            bg=background,
            oauth_url=CHECK_VALIDATE_ACCESS_TOKEN_ENDPOINT,
            trailhub_url=API_TRAILHUB_ENDPOINT,
            source=settings.APP_NAME.lower(),
            message=f"has regenerate api key {str(id)}",
            user_id=str(user_id),
        )

    return await doc.regenerate_api_key(id=id, user_id=doc.user_id)


@router.put(
    "/{id}/action",
    dependencies=[
        Depends(CheckAccessAllow(url=CHECK_ACCESS_ALLOW_ENDPOINT, permissions={"apikey:can-activate-or-deactivate-apikey"})),
    ],
    response_model=APIKeyDocument,
    response_model_by_alias=True,
    response_model_exclude={"hashed_key"},
    summary="Activate or deactivate API Key by ID (Soft Update)",
    status_code=status.HTTP_202_ACCEPTED,
)
async def activate_or_deactivate_apikey(
    request: Request,
    background: BackgroundTasks,
    id: PydanticObjectId,
    action: Literal["activate", "deactivate"],
    token_info: dict = Depends(VerifyAccessToken(url=CHECK_VALIDATE_ACCESS_TOKEN_ENDPOINT)),
):
    doc = await find_document(document=APIKeyDocument, query={"_id": id}, status_code=status.HTTP_400_BAD_REQUEST)

    user_info = token_info.get("user_info", {})
    user_id = user_info.get("_id")

    if user_id != str(doc.user_id) and not user_info.get("role", {}).get("slug") != slugify(settings.ROLE_SUPER_ADMIN):
        raise CustomHTTPException(
            code_error=APIKeyErrorCode.CANNOT_ACCESS_RESOURCE,
            message_error="You cannot access this resource",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    if settings.USE_TRACK_ACTIVITY_LOGS:
        await send_event(
            request=request,
            bg=background,
            oauth_url=CHECK_VALIDATE_ACCESS_TOKEN_ENDPOINT,
            trailhub_url=API_TRAILHUB_ENDPOINT,
            source=settings.APP_NAME.lower(),
            message=f"has {action} api key {str(id)}",
            user_id=str(user_id),
        )

    is_active = True if action == "activate" else False
    return await doc.set({"is_active": is_active, "updated_at": datetime.now(timezone.utc)})


@router.delete(
    "/{id}",
    dependencies=[
        Depends(CheckAccessAllow(url=CHECK_ACCESS_ALLOW_ENDPOINT, permissions={"apikey:can-delete-apikey"})),
    ],
    summary="Delete API Key by ID (Soft Delete)",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove(
    request: Request,
    background: BackgroundTasks,
    id: PydanticObjectId,
    token_info: dict = Depends(VerifyAccessToken(url=CHECK_VALIDATE_ACCESS_TOKEN_ENDPOINT)),
):
    user_id = token_info.get("user_info", {}).get("_id")

    if settings.USE_TRACK_ACTIVITY_LOGS:
        await send_event(
            request=request,
            bg=background,
            oauth_url=CHECK_VALIDATE_ACCESS_TOKEN_ENDPOINT,
            trailhub_url=API_TRAILHUB_ENDPOINT,
            source=settings.APP_NAME.lower(),
            message=f"has delete api key {str(id)}",
            user_id=str(user_id),
        )

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
