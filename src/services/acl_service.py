from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.security.session_manager import UserInfo
from src.tools.meta_acl_client import MetaAclClient


class AclService:
    def __init__(self, db: AsyncSession, meta_acl: MetaAclClient) -> None:
        self.db = db
        self.meta_acl = meta_acl

    async def get_list_without_acl(self, user: UserInfo) -> dict[str, Any]:
        # TODO: Meta 서비스에서 사용자/그룹 라이트 목록 조회 및 가공
        return {"users": [], "groups": []}

    async def get_acl_list(self, contents_id: int, content_type: str, user: UserInfo) -> dict[str, Any]:
        # TODO: Meta ACL API 호출 및 ACL/후보 목록 가공
        return {"contentsId": contents_id, "type": content_type, "acl": []}

    async def set_acl_list(self, contents_ids: list[int], payload: dict[str, Any], user: UserInfo) -> bool:
        # TODO: content.ids 포맷으로 Meta ACL 업데이트 API 호출
        return True

