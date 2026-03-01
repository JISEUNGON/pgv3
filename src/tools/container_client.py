from __future__ import annotations

from typing import Any, Dict, List, Optional

from datetime import datetime, timedelta

from httpx import Response

from src.tools.http_client import HttpClient


class ContainerClient:
    """
    pgv2 ContainerManagementService 를 Python 으로 포팅한 컨테이너 관리 API 래퍼.
    - base_url: IRISProperties.server.containerManagement 에 해당
    """

    def __init__(self, base_url: str, http_client: HttpClient | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.http = http_client or HttpClient()

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Response:
        url = f"{self.base_url}/v1/{path.lstrip('/')}"
        return await self.http.get(url, params=params)

    async def _post(self, path: str, body: Optional[Dict[str, Any]] = None) -> Response:
        url = f"{self.base_url}/v1/{path.lstrip('/')}"
        return await self.http.post(url, json=body or {})

    @staticmethod
    def _conv_expire_at(expire_date: datetime.date, is_limit: bool = False) -> str:
        if is_limit:
            return "-1"
        next_day = expire_date + timedelta(days=1)
        dt = datetime.combine(next_day, datetime.min.time())
        return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    def _conv_params(
        self,
        image: str,
        backup_id: Optional[str],
        cpu: int,
        gpu: int,
        mem: int,
        capacity: int,
        expire_date,
        is_limit: bool,
    ) -> Dict[str, Any]:
        resource = {
            "cpu": cpu * 1000,
            "gpu": gpu,
            "mem": mem,
            "capacity": capacity,
        }
        params: Dict[str, Any] = {"resource": resource}
        if backup_id:
            params["backupId"] = backup_id
        elif image:
            params["image"] = image
        else:
            raise ValueError("Missing arguments image or backupId.")
        params["expireAt"] = self._conv_expire_at(expire_date, is_limit)
        return params

    async def get_resource_info(self) -> Dict[str, Any]:
        resp = await self._get("resource-info")
        resp.raise_for_status()
        return resp.json()

    async def get_create_info(self) -> Dict[str, Any]:
        resp = await self._get("create-info")
        resp.raise_for_status()
        return resp.json()

    async def get_available_resource(self) -> Dict[str, Any]:
        resp = await self._get("available-resource")
        resp.raise_for_status()
        return resp.json()

    async def get_create_types(self) -> Dict[str, Any]:
        resp = await self._get("container/type")
        resp.raise_for_status()
        return resp.json()

    async def get_container_list(self) -> Dict[str, Any]:
        resp = await self._post("containers")
        resp.raise_for_status()
        return resp.json()

    async def get_container_one(self, container_id: str) -> Dict[str, Any]:
        resp = await self._get(f"container/{container_id}")
        resp.raise_for_status()
        return resp.json()

    async def create_container_with_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        resp = await self._post("container/create", params)
        resp.raise_for_status()
        return resp.json()

    async def create_container(
        self,
        image: str,
        backup_id: Optional[str],
        cpu: int,
        gpu: int,
        mem: int,
        capacity: int,
        expire_date,
        is_limit: bool,
    ) -> Dict[str, Any]:
        params = self._conv_params(image, backup_id, cpu, gpu, mem, capacity, expire_date, is_limit)
        return await self.create_container_with_params(params)

    async def stop_container(self, container_id: str) -> Dict[str, Any]:
        params = {"id": container_id}
        resp = await self._post("container/stop", params)
        resp.raise_for_status()
        return resp.json()

    async def expire_container(self, container_id: str) -> Dict[str, Any]:
        params = {"id": container_id}
        resp = await self._post("container/expire", params)
        resp.raise_for_status()
        return resp.json()

    async def restart_container_with_params(self, container_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        params = dict(params)
        params["id"] = container_id
        resp = await self._post("container/restart", params)
        resp.raise_for_status()
        return resp.json()

    async def restart_container(
        self,
        container_id: str,
        image: str,
        backup_id: Optional[str],
        cpu: int,
        gpu: int,
        mem: int,
        capacity: int,
        expire_date,
        is_limit: bool,
    ) -> Dict[str, Any]:
        params = self._conv_params(image, backup_id, cpu, gpu, mem, capacity, expire_date, is_limit)
        return await self.restart_container_with_params(container_id, params)

    async def change_info_container(self, container_id: str, expire_date, is_limit: bool) -> Dict[str, Any]:
        params = {"id": container_id, "expireAt": self._conv_expire_at(expire_date, is_limit)}
        resp = await self._post("container/setting", params)
        resp.raise_for_status()
        return resp.json()

    async def delete_container(self, container_id: str) -> Dict[str, Any]:
        params = {"id": container_id}
        resp = await self._post("container/delete", params)
        resp.raise_for_status()
        return resp.json()

    async def get_explorer(self, container_id: str, dirpath: str, depth: int = 0, type_: str = "all") -> Dict[str, Any]:
        params: Dict[str, Any] = {"id": container_id, "path": dirpath, "depth": depth, "type": type_}
        resp = await self._post("container/explorer", params)
        resp.raise_for_status()
        return resp.json()

    async def import_data(self, container_id: str, dirpath: str, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        params = {"id": container_id, "path": dirpath, "files": files}
        resp = await self._post("container/data-import", params)
        resp.raise_for_status()
        return resp.json()

    async def export_data(self, container_id: str, dirpath: str, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        params = {"id": container_id, "path": dirpath, "files": files}
        resp = await self._post("container/data-export", params)
        resp.raise_for_status()
        return resp.json()

    async def get_backup_list(
        self,
        is_share: Optional[bool],
        image_id: Optional[str],
        user_id: Optional[str],
        query: Optional[str],
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if is_share is not None:
            params["isShare"] = is_share
        if image_id:
            params["imageId"] = image_id
        if user_id:
            params["userId"] = user_id
        if query:
            params["query"] = query
        resp = await self._post("backup/containers", params)
        resp.raise_for_status()
        return resp.json()

    async def get_backup_info(self, backup_id: str) -> Dict[str, Any]:
        resp = await self._get(f"backup/info", params={"backupId": backup_id})
        resp.raise_for_status()
        return resp.json()

    async def get_backup_status(self, container_id: str) -> Dict[str, Any]:
        params = {"containerId": container_id}
        resp = await self._get("backup/status", params=params)
        resp.raise_for_status()
        return resp.json()

    async def exist_backup_name(self, backup_id: Optional[str], image_id: str, user_id: str, backup_title: str) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "imageId": image_id,
            "userId": user_id,
            "backupTitle": backup_title,
        }
        if backup_id:
            params["backupId"] = backup_id
        resp = await self._post("backup/check", params)
        resp.raise_for_status()
        return resp.json()

    async def create_backup(
        self,
        container_id: str,
        user_id: str,
        tool_owner_id: str,
        backup_title: str,
        is_share: bool,
        description: str,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "containerId": container_id,
            "containerOwnerId": tool_owner_id,
            "userId": user_id,
            "backupTitle": backup_title,
            "description": description,
            "isShare": is_share,
        }
        resp = await self._post("backup", params)
        resp.raise_for_status()
        return resp.json()

    async def update_backup(self, backup_id: str, backup_title: str, description: str, is_share: bool) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "backupId": backup_id,
            "backupTitle": backup_title,
            "description": description,
            "isShare": is_share,
        }
        resp = await self._post("backup/edit", params)
        resp.raise_for_status()
        return resp.json()

    async def delete_backup(self, backup_id: str) -> Dict[str, Any]:
        params = {"backupId": backup_id}
        resp = await self._post("backup/delete", params)
        resp.raise_for_status()
        return resp.json()


