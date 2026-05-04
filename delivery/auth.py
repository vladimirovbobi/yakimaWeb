"""JWT verification — must match Django SimpleJWT signature."""
from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass

import jwt
from fastapi import Header, HTTPException

from config import get_settings


@dataclass
class AuthenticatedUser:
    user_id: int
    is_realtor: bool
    is_vendor: bool
    is_staff: bool


def verify_jwt(token: str) -> AuthenticatedUser:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.django_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="token_expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="invalid_token") from exc

    if payload.get("token_type") != "access":
        raise HTTPException(status_code=401, detail="invalid_token_type")

    user_id = payload.get("user_id")
    if not isinstance(user_id, int):
        raise HTTPException(status_code=401, detail="invalid_user_id")

    return AuthenticatedUser(
        user_id=user_id,
        is_realtor=bool(payload.get("is_realtor", False)),
        is_vendor=bool(payload.get("is_vendor", False)),
        is_staff=bool(payload.get("is_staff", False)),
    )


async def auth_dependency(
    authorization: str | None = Header(default=None),
    cookie: str | None = Header(default=None),
) -> AuthenticatedUser:
    """Accept either ``Authorization: Bearer <jwt>`` or the ``yw_access`` cookie."""
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    elif cookie:
        for kv in cookie.split(";"):
            kv = kv.strip()
            if kv.startswith("yw_access="):
                token = kv.split("=", 1)[1]
                break
    if not token:
        raise HTTPException(status_code=401, detail="missing_token")
    return verify_jwt(token)


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """HMAC-SHA256 — used when this service calls back to Django."""
    settings = get_settings()
    expected = hmac.new(
        settings.delivery_webhook_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
