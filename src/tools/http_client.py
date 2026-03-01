from __future__ import annotations

from typing import Any

import httpx


class HttpClient:
    """
    공통 HTTP 클라이언트 헬퍼.
    """

    def __init__(self) -> None:
        self._client = httpx.AsyncClient()

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self._client.get(url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self._client.post(url, **kwargs)

