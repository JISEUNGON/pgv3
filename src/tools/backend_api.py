from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from src.tools.backend_response import BackendResponse
from src.utils.logging import get_logger

logger = get_logger(__name__)


class BackendAPI:
    """
    pgv2 BackendAPI 의 Python 버전.
    - serverUrl + uriParts (+ query) 로 URL 을 만들고
    - HTTP GET/POST 를 호출해 BackendResponse 로 감싸서 반환한다.
    """

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self.client = client or httpx.AsyncClient()

    @staticmethod
    def _make_url(server_url: str, uri_parts: str) -> str:
        return "/".join([server_url.rstrip("/"), uri_parts.lstrip("/")])

    @classmethod
    def _make_url_with_query(cls, server_url: str, uri_parts: str, query: Optional[Dict[str, str]]) -> str:
        base = cls._make_url(server_url, uri_parts)
        if not query:
            return base
        query_str = "&".join(f"{k}={v}" for k, v in query.items())
        return f"{base}?{query_str}"

    async def request_get(
        self,
        server_url: str,
        uri_parts: str,
        query: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> BackendResponse:
        url = self._make_url_with_query(server_url, uri_parts, query)
        logger.info("GET %s", url)
        resp = await self.client.get(url, headers=headers)
        try:
            body = resp.json()
        except ValueError:
            return BackendResponse(code=str(resp.status_code), errorMsg="Invalid JSON body", data=None)
        backend = BackendResponse.from_body(body)
        return backend

    async def request_post(
        self,
        server_url: str,
        uri_parts: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> BackendResponse:
        url = self._make_url(server_url, uri_parts)
        body = params or {}
        logger.info("POST %s", url)
        logger.debug("POST params: %s", body)
        resp = await self.client.post(url, json=body, headers=headers)
        try:
            json_body = resp.json()
        except ValueError:
            return BackendResponse(code=str(resp.status_code), errorMsg="Invalid JSON body", data=None)
        backend = BackendResponse.from_body(json_body)
        return backend

