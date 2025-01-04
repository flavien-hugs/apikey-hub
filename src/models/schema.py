from typing import Union

from beanie import PydanticObjectId
from pydantic import BaseModel, Field


class APIKeyBaseSchema(BaseModel):
    user_id: Union[str, PydanticObjectId] = Field(..., description="The user ID that the API key belongs to")
    is_internal: bool = Field(False, title="Is Internal", description="Whether the user is internal or not")
