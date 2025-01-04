import hashlib
import secrets
from hmac import compare_digest, HMAC
from typing import Union

from beanie import PydanticObjectId

from src.config import settings


def generate_api_key(user_id: Union[str, PydanticObjectId]) -> str:
    """
    Generates both raw and hashed API key
    """

    raw_key = f"{secrets.token_hex(settings.TOKEN_SECRET_HEX_LENGTH)}.{str(user_id)}"

    # Create hashed version for storage
    secret_bytes = settings.SECRET_KEY_HASHED.encode('utf-8')
    hmac_obj = HMAC(key=secret_bytes, msg=raw_key.encode('utf-8'), digestmod=hashlib.sha256)
    hashed_key = hmac_obj.hexdigest()

    # Create final API key with prefix
    prefix = f"{settings.API_KEY_PREFIX}_live_" if settings.USE_LIVE_CLIENT else f"{settings.API_KEY_PREFIX}_test_"
    final_api_key = f"{prefix}{hashed_key}"

    return final_api_key


def verify_api_key(provided_key: str, stored_key: str) -> bool:
    """
    Verifies a provided API key against stored key
    """

    prefix = f"{settings.API_KEY_PREFIX}_live_" if settings.USE_LIVE_CLIENT else f"{settings.API_KEY_PREFIX}_test_"
    if not provided_key.startswith(prefix):
        return False

    provided_hash = provided_key[len(prefix):]

    return compare_digest(provided_hash, stored_key)
