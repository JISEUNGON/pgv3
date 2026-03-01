from __future__ import annotations

from typing import Any, Dict, List, Optional

from httpx import Response

from src.tools.http_client import HttpClient


class MetaClient:
    """
    pgv2 MetaService 를 Python 으로 포팅한 클라이언트.
    - base_url: IRISProperties.server.meta 에 해당
    - 토큰 헤더 이름/값은 호출 측에서 headers 로 전달하도록 한다.
    """

    def __init__(self, base_url: str, http_client: HttpClient | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.http = http_client or HttpClient()

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Response:
        url = f"{self.base_url}{path}"
        return await self.http.get(url, params=params, headers=headers)

    async def _post(self, path: str, body: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Response:
        url = f"{self.base_url}{path}"
        return await self.http.post(url, json=body, headers=headers)

    async def get_user_list_lite(self, headers: Dict[str, str]) -> List[Dict[str, Any]]:
        resp = await self._get("/api/account", headers=headers)
        resp.raise_for_status()
        data = resp.json()
        org_list = data.get("data", [])
        simple_list: List[Dict[str, Any]] = []
        for org in org_list:
            simple_list.append(
                {
                    "userId": org.get("userId"),
                    "name": org.get("name"),
                }
            )
        return simple_list

    async def get_group_list_lite(self, headers: Dict[str, str]) -> List[Dict[str, Any]]:
        resp = await self._get("/api/group", headers=headers)
        resp.raise_for_status()
        data = resp.json()
        org_list = data.get("data", [])
        simple_list: List[Dict[str, Any]] = []
        for org in org_list:
            simple_list.append(
                {
                    "groupId": org.get("groupId"),
                    "groupName": org.get("groupName"),
                    "isDefault": str(org.get("isDefault")) == "true",
                }
            )
        return simple_list

    async def get_acl_list(self, category: str, contents_id: str, headers: Dict[str, str]) -> List[Dict[str, Any]]:
        params = {"category": category, "id": contents_id}
        resp = await self._get("/acl", params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data.get("aclList", [])

    async def get_acl_id_list(self, category: str, headers: Dict[str, str], contents_id: str | None = None, user: Dict[str, Any] | None = None) -> List[str]:
        params: Dict[str, str] = {"category": category}
        if contents_id is not None:
            params["id"] = contents_id
        if user is not None:
            params["userId"] = user.get("userId", "")
            params["groupId"] = user.get("groupId", "")
        resp = await self._get("/acl/ids", params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data.get("list", [])

    async def set_acl_list(self, category: str, body: Dict[str, Any], headers: Dict[str, str]) -> bool:
        body = dict(body)
        body["category"] = category
        resp = await self._post("/acl/update/multi", body, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return bool(data.get("success", False))

    async def delete_acl_list(self, category: str, ids: List[str], headers: Dict[str, str]) -> bool:
        body: Dict[str, Any] = {"category": category, "ids": ids}
        resp = await self._post("/acl/delete/multi", body, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return bool(data.get("success", False))

