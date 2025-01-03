from fastapi import APIRouter, Body, status

from src.models import APIKeyBaseSchema, APIKeyDocument

router = APIRouter(prefix="/keys", tags=["API KEYS"])


@router.post(
    "",
    response_model=APIKeyDocument,
    summary="Create API Key",
    status_code=status.HTTP_201_CREATED,
)
async def create(payload: APIKeyBaseSchema = Body(...)):
    new_doc = await APIKeyDocument(**payload.model_dump()).create()
    return new_doc
