from __future__ import annotations

from typing import Any, Dict

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.tools.graphio_client import GraphioClient


class GraphioService:
    """
    pgv2 GraphioService 역할을 Python 으로 포팅한 서비스.
    FastAPI 엔드포인트에서 access_token 과 params 를 받아 GraphioClient 로 전달한다.
    """

    def __init__(self, db: AsyncSession, client: GraphioClient) -> None:
        self.db = db
        self.client = client
        self.settings = get_settings()

    def _compat_iris(self) -> dict[str, Any]:
        compat = self.settings.compat if isinstance(self.settings.compat, dict) else {}

        iris = compat.get("iris", {})

        return iris if isinstance(iris, dict) else {}

    def _graphio_token_name(self) -> str:
        iris = self._compat_iris()
        token_cfg = iris.get("token", {})

        if isinstance(token_cfg, dict):
            name = token_cfg.get("graphioName") or token_cfg.get("graphio-name")
            if isinstance(name, str) and name.strip():
                return name.strip()
        return "access_token"

    def _extract_graphio_token(self, request: Request) -> str:
        token_name = self._graphio_token_name()
        # pgv2 기본: graphio token name(access_token) 쿠키/헤더
        token = request.cookies.get(token_name) or request.headers.get(token_name)
        if token:
            return token

        # Swagger Authorize 호환: Authorization: Bearer <token>
        auth = request.headers.get("Authorization") or request.headers.get("authorization")
        if auth and auth.lower().startswith("bearer "):
            bearer_token = auth.split(" ", 1)[1].strip()
            if bearer_token:
                return bearer_token

        # pgv2 x-access-token 호환 fallback
        compat = self._compat_iris()
        token_cfg = compat.get("token", {}) if isinstance(compat, dict) else {}
        default_token_name = str(token_cfg.get("name") or "x-access-token")
        token = request.cookies.get(default_token_name) or request.headers.get(default_token_name)
        if token:
            return token

        raise RuntimeError(
            f"(Graphio) token not found. checked: {token_name}, Authorization(Bearer), {default_token_name}"
        )

    async def get_url(self) -> str:
        return self.settings.url.graphio

    async def get_app_list(self, params: Dict[str, Any], request: Request) -> Dict[str, Any]:
        access_token = self._extract_graphio_token(request)
        data = await self.client.get_app_list(params, access_token)
        return data
