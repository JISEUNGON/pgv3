from __future__ import annotations

from typing import Any, Dict, List

from src.tools.http_client import HttpClient


class MetaAclClient:
    """
    MetaService 의 ACL 관련 메서드를 포팅한 클라이언트.
    - base_url: Meta 서버 URL (IRISProperties.server.meta 에 해당)
    - 토큰 헤더는 호출 측에서 전달.
    """

    def __init__(self, base_url: str, http_client: HttpClient | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.http = http_client or HttpClient()

    async def get_acl(self, category: str, contents_id: str, headers: Dict[str, str]) -> List[Dict[str, Any]]:
        from httpx import Response

        params = {"category": category, "id": contents_id}
        url = f"{self.base_url}/acl"
        resp: Response = await self.http.get(url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data.get("aclList", [])

    async def get_acl_ids(self, category: str, headers: Dict[str, str], contents_id: str | None = None, user: Dict[str, Any] | None = None) -> List[str]:
        from httpx import Response

        params: Dict[str, str] = {"category": category}
        if contents_id is not None:
            params["id"] = contents_id
        if user is not None:
            params["userId"] = user.get("userId", "")
            params["groupId"] = user.get("groupId", "")
        url = f"{self.base_url}/acl/ids"
        resp: Response = await self.http.get(url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data.get("list", [])

    async def set_acl(self, category: str, body: Dict[str, Any], headers: Dict[str, str]) -> bool:
        from httpx import Response

        body = dict(body)
        body["category"] = category
        url = f"{self.base_url}/acl/update/multi"
        resp: Response = await self.http.post(url, json=body, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return bool(data.get("success", False))

    async def delete_acl(self, category: str, ids: List[str], headers: Dict[str, str]) -> bool:
        from httpx import Response

        body: Dict[str, Any] = {"category": category, "ids": ids}
        url = f"{self.base_url}/acl/delete/multi"
        resp: Response = await self.http.post(url, json=body, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return bool(data.get("success", False))


