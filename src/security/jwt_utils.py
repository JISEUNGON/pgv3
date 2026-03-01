from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from src.core.config import get_settings
from src.security.session_manager import UserInfo


class InvalidTokenError(Exception):
    pass


def create_access_token(user: UserInfo) -> str:
    settings = get_settings()
    expire_minutes = settings.security.accessTokenExpireMinutes
    expire = datetime.now(tz=timezone.utc) + timedelta(minutes=expire_minutes)
    to_encode = {
        "sub": user.id,
        "name": user.name,
        "groups": user.groups,
        "is_admin": user.is_admin,
        "exp": expire,
    }
    token = jwt.encode(
        to_encode,
        settings.security.jwtSecretKey,
        algorithm=settings.security.jwtAlgorithm,
    )
    return token


def decode_access_token(token: str) -> UserInfo:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.security.jwtSecretKey,
            algorithms=[settings.security.jwtAlgorithm],
        )
    except JWTError as exc:
        raise InvalidTokenError(str(exc)) from exc

    user_id = payload.get("sub")
    if not user_id:
        raise InvalidTokenError("Missing subject in token")

    return UserInfo(
        id=user_id,
        name=payload.get("name", ""),
        groups=payload.get("groups") or [],
        is_admin=bool(payload.get("is_admin", False)),
    )

