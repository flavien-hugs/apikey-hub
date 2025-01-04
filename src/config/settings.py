from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class ApiKeyHubSettings(BaseSettings):
    # APP CONFIG
    APP_TITLE: Optional[str] = Field(
        default="UNSTA: ApiKey HUB", alias="APP_TITLE", description="Title of the application"
    )
    APP_NAME: Optional[str] = Field(default="apikeys-hub", alias="APP_NAME", description="Name of the application")
    APP_HOSTNAME: Optional[str] = Field(
        default="0.0.0.0", alias="APP_HOSTNAME", description="Hostname of the application"
    )
    APP_RELOAD: Optional[bool] = Field(default=True, alias="APP_RELOAD", description="Enable/Disable auto-reload")
    APP_LOG_LEVEL: Optional[str] = Field(
        default="debug", alias="APP_LOG_LEVEL", description="Log level of the application"
    )
    APP_ACCESS_LOG: Optional[bool] = Field(
        default=True, alias="APP_ACCESS_LOG", description="Enable/Disable access log"
    )
    APP_DEFAULT_PORT: Optional[int] = Field(
        default=8800, alias="APP_DEFAULT_PORT", description="Default port of the application"
    )
    ALLOW_ANONYM_PUSH: Optional[bool] = Field(
        default=False, alias="ALLOW_ANONYM_PUSH", description="Allow anonymous push to the config"
    )
    APP_LOOP: Optional[str] = Field(
        default="uvloop", alias="APP_LOOP", description="Type of loop to use: none, auto, asyncio or uvloop"
    )
    API_KEY_PREFIX: Optional[str] = Field(
        default="fhs",
        alias="API_KEY_PREFIX",
        description="Prefix for the API key to be used for authentication purposes",
    )
    USE_LIVE_CLIENT: Optional[bool] = Field(
        default=False, alias="USE_LIVE_CLIENT", description="Use live client for the application"
    )
    TOKEN_SECRET_HEX_LENGTH: Optional[int] = Field(
        default=32, alias="TOKEN_SECRET_HEX_LENGTH", description="Length of the token secret in hex"
    )
    SECRET_KEY_HASHED: Optional[str] = Field(
        ...,
        alias="SECRET_KEY_HASHED",
        description="Hashed secret key to be used for authentication purposes",
    )

    # APP MODEL NAME
    APIKEY_HUB_COLLECTION: str = Field(..., alias="APIKEY_HUB_COLLECTION", description="Name of the model")
    APP_DESC_DB_COLLECTION: str = Field(
        ..., alias="APP_DESC_DB_COLLECTION", description="Collection for app description"
    )
    PERMS_DB_COLLECTION: str = Field(..., alias="PERMS_DB_COLLECTION", description="Collection for permissions")

    # DATABASE CONFIG
    MONGO_DB: str = Field(..., alias="MONGO_DB", description="Name of the config")
    MONGODB_URI: str = Field(..., alias="MONGODB_URI", description="URI of the MongoDB config")

    # VALIDATE TOKEN AND CHECK ACCESS ENDPOINT
    API_AUTH_URL_BASE: Optional[str] = Field(
        default="http://localhost:9000", alias="API_AUTH_URL_BASE", description="Base URL of the authentication service"
    )
    API_AUTH_CHECK_ACCESS_ENDPOINT: Optional[str] = Field(
        default="/check-access", alias="API_AUTH_CHECK_ACCESS_ENDPOINT", description="Endpoint to check access"
    )
    API_AUTH_CHECK_VALIDATE_ACCESS_TOKEN: Optional[str] = Field(
        default="/check-validate-access-token",
        alias="API_AUTH_CHECK_VALIDATE_ACCESS_TOKEN",
        description="Endpoint to validate token",
    )


@lru_cache
def get_settings() -> ApiKeyHubSettings:
    return ApiKeyHubSettings()
