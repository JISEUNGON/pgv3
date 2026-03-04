from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.security.session_manager import UserInfo
from src.tools.container_client import ContainerClient


class BackupService:
    def __init__(self, db: AsyncSession, container_client: ContainerClient) -> None:
        self.db = db
        self.container_client = container_client

    async def get_backup_list(self, user: UserInfo, params: dict[str, Any]) -> list[dict[str, Any]]:
        data = await self.container_client.get_backup_list(
            is_share=params.get("isShare"),
            image_id=params.get("imageId"),
            user_id=params.get("userId"),
            query=params.get("query"),
        )
        return list(data.get("data") or data.get("list") or [])

    async def get_backup_status(self, tool_id: str, user: UserInfo) -> dict[str, Any]:
        data = await self.container_client.get_backup_status(tool_id)
        return {"id": tool_id, "status": data.get("data", data)}

    async def check_backup_exist_name(self, payload: dict[str, Any], user: UserInfo) -> bool:
        data = await self.container_client.exist_backup_name(
            backup_id=payload.get("id"),
            image_id=str(payload.get("imageId") or ""),
            user_id=user.id,
            backup_title=str(payload.get("name") or ""),
        )
        return bool(data.get("data", {}).get("isExist") or data.get("isExist", False))

    async def backup_tool(self, tool_id: str, user: UserInfo, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = payload or {}
        data = await self.container_client.create_backup(
            container_id=tool_id,
            user_id=user.id,
            tool_owner_id=str(body.get("ownerId") or user.id),
            backup_title=str(body.get("name") or ""),
            is_share=bool(body.get("shareYn", False)),
            description=str(body.get("description") or ""),
        )
        return {"id": tool_id, "backup": data.get("data", data)}

    async def update_backup(self, backup_id: int, user: UserInfo, payload: dict[str, Any]) -> dict[str, Any]:
        data = await self.container_client.update_backup(
            backup_id=str(backup_id),
            backup_title=str(payload.get("name") or ""),
            description=str(payload.get("description") or ""),
            is_share=bool(payload.get("shareYn", False)),
        )
        return {"backupId": backup_id, "updated": bool(data)}

    async def delete_backup(self, backup_id: int, user: UserInfo) -> dict[str, Any]:
        data = await self.container_client.delete_backup(str(backup_id))
        return {"backupId": backup_id, "deleted": bool(data)}
