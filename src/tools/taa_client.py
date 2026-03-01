from __future__ import annotations

from typing import Any, Dict

from httpx import Response

from src.tools.http_client import HttpClient


class TaaClient:
    """
    pgv2 TaaService 를 Python 으로 포팅한 Template Analysis Adaptor 연동 클라이언트.
    - base_url: IRISProperties.server.templateAnalysisAdaptor 에 해당
    """

    def __init__(self, base_url: str, http_client: HttpClient | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.http = http_client or HttpClient()

    async def _post(self, path: str, body: Dict[str, Any]) -> Response:
        url = f"{self.base_url}/v1/{path.lstrip('/')}"
        return await self.http.post(url, json=body)

    async def fetch_sample(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Java: bypassPostAPI("sample", body)
        """
        resp = await self._post("sample", body)
        resp.raise_for_status()
        return resp.json()

    async def run_analyze(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Java: bypassPostAPI("analyze", body)
        """
        resp = await self._post("analyze", body)
        resp.raise_for_status()
        return resp.json()

