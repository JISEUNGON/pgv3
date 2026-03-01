from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.entity.file_node import FileNode
from src.security.session_manager import UserInfo


class FileNodeService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_file_node_list_with_count(self, user: UserInfo, params: dict[str, Any]) -> dict[str, Any]:
        # TODO: ACL + 검색 + 페이징 쿼리 구현
        return {"items": [], "total": 0}

    async def rename_file_node(self, node_id: int, new_name: str, user: UserInfo) -> dict[str, Any]:
        # TODO: 실제 FileNode 조회 및 이름 변경 로직 구현
        return {"id": node_id, "renamed": False}

    async def get_exist_file_node_name(self, name: str, node_id: int | None, user: UserInfo) -> bool:
        # TODO: 중복 검사 쿼리 구현
        return False

    async def get_map_file_node_new_name_multi(self, names: list[str], user: UserInfo) -> dict[str, str]:
        # TODO: 중복 시 name (n) 규칙 적용 로직 구현
        return {name: name for name in names}

    async def update_file_object(self, payload: dict[str, Any], user: UserInfo) -> dict[str, Any]:
        # TODO: fileObjectId/fileName/fileSize/sensitive/expireDate 갱신 로직 구현
        return {"updated": False}

