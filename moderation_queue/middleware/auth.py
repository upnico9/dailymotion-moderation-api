import base64

from fastapi import Header

from domain.exceptions import AuthorizationError


def decode_authorization(header: str) -> str:
    try:
        decoded = base64.b64decode(header).decode("utf-8")
    except Exception:
        raise AuthorizationError("Invalid authorization header")

    if not decoded.strip():
        raise AuthorizationError("Invalid authorization header")

    return decoded.strip()


def get_current_moderator(authorization: str = Header(default=None)) -> str:
    if not authorization:
        raise AuthorizationError("Authorization header required")

    return decode_authorization(authorization)
