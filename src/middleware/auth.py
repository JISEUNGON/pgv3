from __future__ import annotations

from fastapi import Depends, Request

from src.exceptions.base import AuthenticationException
from src.security.jwt_utils import InvalidTokenError, decode_access_token
from src.security.session_manager import UserInfo

COOKIE_TOKEN_NAME = "x-access-token"


async def get_current_user(request: Request) -> UserInfo:
    """
    쿠키 x-access-token 에서 JWT 액세스 토큰을 읽어 인증한다.
    """
    token = request.cookies.get(COOKIE_TOKEN_NAME)
    if not token:
        raise AuthenticationException("Missing cookie: x-access-token")
    token = token.strip()

    try:
        return decode_access_token(token)
    except InvalidTokenError:
        raise AuthenticationException("Invalid or expired token")
