from __future__ import annotations

from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from src.tools.graphio_client import GraphioClient


class GraphioService:
    """
    pgv2 GraphioService 역할을 Python 으로 포팅한 서비스.
    FastAPI 엔드포인트에서 access_token 과 params 를 받아 GraphioClient 로 전달한다.
    """

    def __init__(self, db: AsyncSession, client: GraphioClient) -> None:
        self.db = db
        self.client = client

    async def get_url(self) -> Dict[str, Any]:
        url = await self.client.get_url()
        return {"url": url}

    async def get_app_list(self, params: Dict[str, Any], access_token: str) -> Dict[str, Any]:
        data = await self.client.get_app_list(params, access_token)
        return data

