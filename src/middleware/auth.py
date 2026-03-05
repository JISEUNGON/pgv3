from __future__ import annotations

from fastapi import Depends, Request

from src.exceptions.base import AuthenticationException
from src.security.jwt_utils import InvalidTokenError, decode_access_token
from src.security.session_manager import UserInfo

COOKIE_TOKEN_NAME = "x-access-token"
HEADER_AUTH = "authorization"
HEADER_COOKIE = "cookie"
HEADER_TOKEN_NAME = "x-access-token"


def _get_token_from_cookie_header(cookie_header: str) -> str | None:
    """
    Cookie 헤더 문자열에서 x-access-token= 값을 파싱해 꺼낸다.
    예: "locale=ko; x-access-token=eyJ0eXAi...; other=val" -> "eyJ0eXAi..."
    """
    if not cookie_header or not cookie_header.strip():
        return None
    prefix = f"{COOKIE_TOKEN_NAME}="
    prefix_lower = prefix.lower()
    for part in cookie_header.split(";"):
        part = part.strip()
        if part.lower().startswith(prefix_lower):
            value = part[len(prefix) :].strip()
            if value:
                return value
    return None


def _get_token_from_request(request: Request) -> str | None:
    """
    쿠키 또는 요청 헤더에서 JWT 액세스 토큰을 가져온다.
    우선순위: 쿠키 파싱 → Cookie 헤더에서 x-access-token 파싱 → Authorization: Bearer → 헤더(x-access-token)
    """
    # 1. request.cookies (파싱된 쿠키)
    token = request.cookies.get(COOKIE_TOKEN_NAME)
    if token:
        return token.strip()

    # 2. Cookie 헤더 문자열에서 x-access-token 값 직접 파싱 (로그에 나오는 그 형식 대응)
    cookie_header = request.headers.get(HEADER_COOKIE)
    token = _get_token_from_cookie_header(cookie_header or "")
    if token:
        return token

    # 3. Authorization: Bearer <token>
    auth = request.headers.get(HEADER_AUTH)
    if auth and auth.lower().startswith("bearer "):
        return auth[7:].strip()

    # 4. 커스텀 헤더 x-access-token
    token = request.headers.get(HEADER_TOKEN_NAME)
    if token:
        return token.strip()

    return None


async def get_current_user(request: Request) -> UserInfo:
    """
    쿠키 또는 request header에서 JWT 액세스 토큰을 읽어 인증한다.
    """
    print("request path: " + request.url.path)
    print("cookies: " + str(request.cookies))
    print("headers: " + str(request.headers))
    token = _get_token_from_request(request)
    if not token:
        raise AuthenticationException("Missing token: set cookie x-access-token or header Authorization: Bearer <token> or x-access-token")

    try:
        return decode_access_token(token)
    except InvalidTokenError:
        raise AuthenticationException("Invalid or expired token")
