from __future__ import annotations

import json

import httpx
from fastapi import Request, Response

from src.core.config import get_settings
from src.exceptions.base import AuthenticationException
from src.security.jwt_utils import InvalidTokenError, decode_access_token
from src.security.session_manager import UserInfo

COOKIE_TOKEN_NAME = "x-access-token"
HEADER_AUTH = "authorization"
HEADER_COOKIE = "cookie"
HEADER_TOKEN_NAME = "x-access-token"
BRICK_AUTH_SUCCESS = "LOGIN_SUCCESS"


def _token_cookie_name() -> str:
    settings = get_settings()
    compat = settings.compat if isinstance(settings.compat, dict) else {}
    iris = compat.get("iris", {}) if isinstance(compat, dict) else {}
    token_cfg = iris.get("token", {}) if isinstance(iris, dict) else {}
    name = token_cfg.get("name") if isinstance(token_cfg, dict) else None
    return str(name).strip() if isinstance(name, str) and name.strip() else COOKIE_TOKEN_NAME


def _token_cookie_max_age() -> int:
    settings = get_settings()
    compat = settings.compat if isinstance(settings.compat, dict) else {}
    iris = compat.get("iris", {}) if isinstance(compat, dict) else {}
    token_cfg = iris.get("token", {}) if isinstance(iris, dict) else {}
    max_age = token_cfg.get("max-age") if isinstance(token_cfg, dict) else None

    if isinstance(max_age, int) and max_age > 0:
        return max_age
    return max(int(settings.security.accessTokenExpireMinutes) * 60, 1)


def _is_local_login_enabled() -> bool:
    settings = get_settings()
    test = settings.test
    return test is not None


def _brick_auth_url() -> str | None:
    settings = get_settings()
    compat = settings.compat if isinstance(settings.compat, dict) else {}
    iris = compat.get("iris", {}) if isinstance(compat, dict) else {}
    server_cfg = iris.get("server", {}) if isinstance(iris, dict) else {}
    brick_base = server_cfg.get("brick") if isinstance(server_cfg, dict) else None
    if not isinstance(brick_base, str) or not brick_base.strip():
        return None
    return brick_base.rstrip("/") + "/authenticate"


def _extract_x_access_token(body: dict) -> str | None:
    data = body
    if "result" in body and "data" in body:
        try:
            result = int(body.get("result"))
        except (TypeError, ValueError):
            result = 0
        if result != 1:
            return None
        data = body.get("data") if isinstance(body.get("data"), dict) else {}

    if not isinstance(data, dict):
        return None

    status = str(data.get("status") or "").strip()
    if status and status != BRICK_AUTH_SUCCESS:
        return None

    token = data.get("token")
    if isinstance(token, str) and token.strip():
        return token.strip()
    return None


async def _local_login(response: Response) -> UserInfo:
    settings = get_settings()
    test = settings.test
    if test is None:
        raise AuthenticationException("Missing token")

    auth_url = _brick_auth_url()
    if not auth_url:
        raise AuthenticationException("Local login is enabled but compat.iris.server.brick is missing")

    payload = {
        "userId": str(test.user or "").strip(),
        "userPass": str(test.password or "").strip(),
    }
    if not payload["userId"] or not payload["userPass"]:
        raise AuthenticationException("Local login requires test.user and test.password")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(auth_url, json=payload)
    except Exception as exc:
        raise AuthenticationException(f"Brick auth request failed: {exc}") from exc

    if resp.status_code >= 400:
        raise AuthenticationException(f"Brick auth failed: HTTP {resp.status_code}")

    try:
        body = resp.json()
    except json.JSONDecodeError as exc:
        raise AuthenticationException("Brick auth failed: invalid JSON response") from exc

    if not isinstance(body, dict):
        raise AuthenticationException("Brick auth failed: invalid response body")

    x_access_token = _extract_x_access_token(body)
    if not x_access_token:
        raise AuthenticationException("Brick auth failed: token not found")

    cookie_name = _token_cookie_name()
    response.set_cookie(
        key=cookie_name,
        value=x_access_token,
        path="/",
        httponly=True,
        max_age=_token_cookie_max_age(),
    )

    try:
        return decode_access_token(x_access_token)
    except InvalidTokenError as exc:
        raise AuthenticationException(f"Invalid local login token: {exc}") from exc


def _get_token_from_cookie_header(cookie_header: str) -> str | None:
    """
    Cookie 헤더 문자열에서 x-access-token= 값을 파싱해 꺼낸다.
    예: "locale=ko; x-access-token=eyJ0eXAi...; other=val" -> "eyJ0eXAi..."
    """
    if not cookie_header or not cookie_header.strip():
        return None

    token_name = _token_cookie_name()
    prefix = f"{token_name}="
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
    token_name = _token_cookie_name()
    token = request.cookies.get(token_name)
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
    token = request.headers.get(token_name) or request.headers.get(HEADER_TOKEN_NAME)
    if token:
        return token.strip()

    return None


async def get_current_user(request: Request, response: Response) -> UserInfo:
    """
    쿠키 또는 request header에서 JWT 액세스 토큰을 읽어 인증한다.
    """
    token = _get_token_from_request(request)
    if token:
        try:
            return decode_access_token(token)
        except InvalidTokenError:
            # test 설정이 있으면 pgv2 localLogin 과 동일하게 재로그인 시도
            if _is_local_login_enabled():
                return await _local_login(response)
            raise AuthenticationException("Invalid or expired token")

    if _is_local_login_enabled():
        return await _local_login(response)

    token_name = _token_cookie_name()
    raise AuthenticationException(
        f"Missing token: set cookie {token_name} or header Authorization: Bearer <token> or {token_name}"
    )
