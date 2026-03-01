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
        # TODO: 권한 정책에 따른 백업 목록 조회 구현
        return []

    async def get_backup_status(self, tool_id: int, user: UserInfo) -> dict[str, Any]:
        # TODO: 컨테이너 기준 백업 상태 조회
        return {"id": tool_id}

    async def check_backup_exist_name(self, name: str, user: UserInfo) -> bool:
        # TODO: 백업명 중복 체크
        return False

    async def backup_tool(self, tool_id: int, user: UserInfo) -> dict[str, Any]:
        # TODO: 컨테이너 백업 생성 및 메타 저장
        return {"id": tool_id}

    async def update_backup(self, backup_id: int, user: UserInfo, payload: dict[str, Any]) -> dict[str, Any]:
        # TODO: 수정 권한 체크 및 변경
        return {"backupId": backup_id}

    async def delete_backup(self, backup_id: int, user: UserInfo) -> dict[str, Any]:
        # TODO: 권한 체크 후 백업 삭제
        return {"backupId": backup_id}

