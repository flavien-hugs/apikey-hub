from datetime import datetime, timedelta, timezone
from typing import Optional

import pymongo
from beanie import Document, PydanticObjectId
from pydantic import Field

from src.config import settings
from src.shared import generate_api_key
from .schema import APIKeyBaseSchema


class APIKeyDocument(Document, APIKeyBaseSchema):
    api_key: str = Field(..., description="The API key to be used for authentication purposes (read-only)")
    hashed_key: str = Field(..., description="The hashed version of the API key to be stored in the database (read-only)")
    is_active: Optional[bool] = Field(default=True, description="Whether the API key is active or not (read-only)")
    last_used_at: Optional[datetime] = Field(
        default=datetime.now(timezone.utc), description="The date and time the API key was last used (read-only)"
    )
    expires_at: Optional[datetime] = Field(
        default=datetime.now(timezone.utc) + timedelta(days=365),
        description="The date and time the API key will expire (read-only)",
    )
    created_at: Optional[datetime] = Field(
        default=datetime.now(timezone.utc), description="The date and time the API key was created (read-only)"
    )
    updated_at: Optional[datetime] = Field(
        default=datetime.now(timezone.utc), description="The date and time the API key was last updated (read-only)"
    )

    class Settings:
        use_state_management = True
        name = settings.APIKEY_HUB_COLLECTION.split(".")[1]
        indexes = [
            pymongo.IndexModel(
                keys=[("api_key", pymongo.ASCENDING), ("user_id", pymongo.ASCENDING)],
                unique=True,
                background=True,
            )
        ]

    @classmethod
    async def regenerate_api_key(cls, id: PydanticObjectId, user_id: PydanticObjectId):
        api_key, hashed_key = generate_api_key(user_id=user_id)
        updated = await cls.find_one({"_id": id}).update_one({"$set": {"api_key": api_key, "hashed_key": hashed_key}})
        if not updated.acknowledged:
            raise ValueError("API Key not found")
        return await cls.find_one({"_id": id})
