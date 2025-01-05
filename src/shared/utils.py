import hashlib
import secrets
from hmac import compare_digest, HMAC
from typing import Optional, Union

from beanie import Document, PydanticObjectId

from src.common.helpers.error_codes import AppErrorCode
from src.common.helpers.exception import CustomHTTPException
from src.config import settings


def generate_api_key(user_id: Union[str, PydanticObjectId]) -> tuple[str, str]:
    """
    Generates both raw and hashed API key
    """

    # Générer la clé brute avec user_id
    raw_key = f"{secrets.token_hex(settings.TOKEN_SECRET_HEX_LENGTH)}{str(user_id)}"

    # Créer la version complète avec préfixe
    prefix = f"{settings.API_KEY_PREFIX}_live_" if settings.USE_LIVE_CLIENT else f"{settings.API_KEY_PREFIX}_test_"
    final_api_key = f"{prefix}{raw_key}"

    # Créer la version hashée pour stockage
    secret_bytes = settings.SECRET_KEY_HASHED.encode("utf-8")
    hmac_obj = HMAC(key=secret_bytes, msg=raw_key.encode("utf-8"), digestmod=hashlib.sha256)
    hashed_key = hmac_obj.hexdigest()

    return final_api_key, hashed_key


def parse_api_key(key: str):
    """
    Parse and validate API key format
    """
    prefix = f"{settings.API_KEY_PREFIX}_live_" if settings.USE_LIVE_CLIENT else f"{settings.API_KEY_PREFIX}_test_"

    if not key.startswith(prefix):
        return False, None, None

    raw_key = key[len(prefix) :]  # noqa: E203
    expected_length = settings.TOKEN_SECRET_HEX_LENGTH * 2

    if len(raw_key) <= expected_length:
        return False, None, None

    user_id = raw_key[expected_length:]
    return True, raw_key, user_id


def verify_api_key(provided_key: str, stored_hash: str):
    """
    Verifies a provided API key against stored key
    """

    # Valider format et extraire les composants
    is_valid, raw_key, user_id = parse_api_key(provided_key)
    if not is_valid:
        return False, None

    secret_bytes = settings.SECRET_KEY_HASHED.encode("utf-8")
    calculated_hash = HMAC(key=secret_bytes, msg=raw_key.encode("utf-8"), digestmod=hashlib.sha256).hexdigest()

    return compare_digest(calculated_hash, stored_hash), user_id


async def find_document(document: type[Document], query: dict, status_code) -> Optional[Document]:
    """
    Check if document exists in the database
    """

    if (doc := await document.find_one(query)) is None:
        raise CustomHTTPException(
            code_error=AppErrorCode.DOCUMENT_NOT_FOUND,
            message_error="Document not found",
            status_code=status_code,
        )

    return doc
