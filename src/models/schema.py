from typing import Optional, Union
from datetime import datetime
from beanie import PydanticObjectId
from pydantic import BaseModel, Field


class APIKeyBaseSchema(BaseModel):
    user_id: Union[str, PydanticObjectId] = Field(..., description="The user ID that the API key belongs to")


class APIKeyFilterSchema(BaseModel):
    user_id: Optional[Union[str, PydanticObjectId]] = Field(None, description="The user ID that the API key belongs to")
    is_active: Optional[bool] = Field(None, title="Is Active", description="Whether the API key is active or not")
    last_used_at: Optional[datetime] = Field(
        None, title="Last Used At", description="The date and time the API key was last used"
    )
    expires_at: Optional[datetime] = Field(
        None, title="Expires At", description="The date and time the API key will expire"
    )
    created_at: Optional[datetime] = Field(
        None, title="Created At", description="The date and time the API key was created"
    )
