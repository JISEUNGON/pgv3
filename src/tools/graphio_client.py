from __future__ import annotations

from typing import Any, Dict

from httpx import Response

from src.tools.http_client import HttpClient


class GraphioClient:
    """
    pgv2 GraphioService 에 해당하는 Graphio API 연동 클라이언트.
    - base_url: IRISProperties.server.graphio 에 해당
    """

    def __init__(self, base_url: str, http_client: HttpClient | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.http = http_client or HttpClient()

    async def get_url(self) -> str:
        # 단순 base_url 을 반환
        return self.base_url

    async def get_app_list(self, params: Dict[str, Any], access_token: str) -> Dict[str, Any]:
        """
        POST {graphio}/api/app/pgv2/list 를 호출한다.
        Java: GraphioService.bypassPostAPI("api/app/pgv2/list", params)
        """
        url = f"{self.base_url}/api/app/pgv2/list"
        headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}
        resp: Response = await self.http.post(url, json=params, headers=headers)
        resp.raise_for_status()
        return resp.json()


