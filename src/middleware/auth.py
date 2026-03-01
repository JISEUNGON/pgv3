from __future__ import annotations

from typing import Optional

from fastapi import Header

from src.exceptions.base import AuthenticationException
from src.security.jwt_utils import InvalidTokenError, decode_access_token
from src.security.session_manager import UserInfo, get_session_manager


async def get_current_user(
    authorization: Optional[str] = Header(default=None),
) -> UserInfo:
    """
    Authorization: Bearer <token> 헤더를 사용해 인증한다.
    - 우선 JWT 액세스 토큰으로 해석을 시도
    - JWT 해석에 실패하면 세션 토큰으로 간주하고 SessionManager 조회
    """

    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthenticationException("Missing Authorization header")

    token = authorization.split(" ", 1)[1].strip()

    # 1) JWT 토큰 시도
    try:
        return decode_access_token(token)
    except InvalidTokenError:
        # 2) 세션 토큰 시도
        manager = get_session_manager()
        user = manager.get_user(token)
        if not user:
            raise AuthenticationException("Invalid or expired token")
        return user

