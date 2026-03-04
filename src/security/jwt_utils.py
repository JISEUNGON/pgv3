from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from src.core.config import get_settings
from src.security.session_manager import UserInfo, is_system_admin_role


class InvalidTokenError(Exception):
    pass


def create_access_token(user: UserInfo) -> str:
    settings = get_settings()
    expire_minutes = settings.security.accessTokenExpireMinutes
    expire = datetime.now(tz=timezone.utc) + timedelta(minutes=expire_minutes)
    group_id = user.group_id or (user.groups[0] if user.groups else None)
    group_name = user.group_name or group_id
    role_code = user.role_code or ("ROOT" if user.is_admin else "USER")
    is_system_admin = is_system_admin_role(role_code)
    role_name = user.role_name or ("System Admin" if is_system_admin else "User")

    to_encode = {
        # legacy claims
        "sub": user.id,
        "name": user.name,
        "groups": user.groups,
        "is_admin": is_system_admin,
        # pgv2-aligned claims
        "userId": user.id,
        "groupId": group_id,
        "groupName": group_name,
        "roleCode": role_code,
        "isSystemAdmin": is_system_admin,
        "roleName": role_name,
        "email": user.email,
        "phone": user.phone,
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

    user_id = payload.get("userId") or payload.get("sub")
    if not user_id:
        raise InvalidTokenError("Missing subject in token")

    groups = payload.get("groups") or []
    if not isinstance(groups, list):
        groups = []
    group_id = payload.get("groupId") or (groups[0] if groups else None)
    group_name = payload.get("groupName") or group_id
    role_code = payload.get("roleCode")
    is_system_admin = payload.get("isSystemAdmin")
    if is_system_admin is None:
        if role_code is not None:
            is_system_admin = is_system_admin_role(str(role_code))
        else:
            is_system_admin = bool(payload.get("is_admin", False))
    role_name = payload.get("roleName") or ("System Admin" if is_system_admin else "User")

    return UserInfo(
        id=user_id,
        name=payload.get("name", ""),
        groups=groups,
        is_admin=bool(is_system_admin),
        group_id=group_id,
        group_name=group_name,
        role_code=role_code,
        role_name=role_name,
        email=payload.get("email"),
        phone=payload.get("phone"),
    )
