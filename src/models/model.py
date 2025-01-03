from datetime import datetime, timedelta, timezone
from typing import Optional

import pymongo
from beanie import after_event, before_event, Document, Insert, Update
from pydantic import Field

from src.config import settings
from src.shared import generate_api_key
from .schema import APIKeyBaseSchema


class APIKeyDocument(Document, APIKeyBaseSchema):
    api_key: Optional[str] = Field(None, description="The API key to be used for authentication purposes (read-only)")
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

    @before_event([Insert, Update])
    async def generate_api_key(self, **kwargs):
        hashed_key = generate_api_key(self.user_id)
        print("Generated API Key :: ", hashed_key)
        if not await self.find_one({"api_key": hashed_key}).exists():
            self.api_key = hashed_key
        self.api_key = hashed_key
