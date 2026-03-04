from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.security.session_manager import UserInfo
from src.tools.meta_acl_client import MetaAclClient
from src.tools.meta_client import MetaClient


class AclService:
    def __init__(self, db: AsyncSession, meta_acl: MetaAclClient) -> None:
        self.db = db
        self.meta_acl = meta_acl
        settings = get_settings()
        meta_url = settings.url.meta if settings.url and settings.url.meta else ""
        self.meta = MetaClient(meta_url) if meta_url else None

    @staticmethod
    def _as_acl_category(content_type: str) -> str:
        if content_type == "analysis-tool":
            return "analysis-tool"
        if content_type == "file-node":
            return "file-node"
        return content_type

    @staticmethod
    def _auth_headers(user: UserInfo) -> dict[str, str]:
        # pgv2 는 세션/인터셉터로 사용자 컨텍스트를 넘겼다.
        # pgv3 에서는 최소 사용자 컨텍스트를 헤더로 전달한다.
        return {
            "X-User-Id": user.id,
            "X-User-Name": user.name,
        }

    async def get_list_without_acl(self, user: UserInfo) -> dict[str, Any]:
        if self.meta is None:
            return {
                "user": {"isEveryone": False, "acl": [], "list": []},
                "group": {"isEveryone": False, "acl": [], "list": []},
            }

        headers = self._auth_headers(user)
        user_list = await self.meta.get_user_list_lite(headers=headers)
        group_list = await self.meta.get_group_list_lite(headers=headers)

        user_list = [u for u in user_list if u.get("userId") != user.id]

        return {
            "user": {"isEveryone": False, "acl": [], "list": user_list},
            "group": {"isEveryone": False, "acl": [], "list": group_list},
        }

    async def get_acl_list(self, contents_id: int, content_type: str, user: UserInfo) -> dict[str, Any]:
        if self.meta is None:
            return {
                "user": {"isEveryone": False, "acl": [], "list": []},
                "group": {"isEveryone": False, "acl": [], "list": []},
            }

        category = self._as_acl_category(content_type)
        headers = self._auth_headers(user)

        acl_list = await self.meta.get_acl_list(
            category=category,
            contents_id=str(contents_id),
            headers=headers,
        )
        user_list = await self.meta.get_user_list_lite(headers=headers)
        group_list = await self.meta.get_group_list_lite(headers=headers)
        user_list = [u for u in user_list if u.get("userId") != user.id]

        acl_user: list[dict[str, Any]] = []
        acl_group: list[dict[str, Any]] = []
        is_everyone_user = False
        is_everyone_group = False

        for acl in acl_list:
            acl_type = acl.get("type")
            value = acl.get("value")
            if acl_type == "USER":
                if value == "EVERYONE":
                    is_everyone_user = True
                else:
                    found = next((u for u in user_list if u.get("userId") == value), None)
                    if found:
                        acl_user.append(found)
            elif acl_type == "GROUP":
                if value == "EVERYONE":
                    is_everyone_group = True
                else:
                    found = next((g for g in group_list if g.get("groupId") == value), None)
                    if found:
                        acl_group.append(found)

        user_acl_ids = {str(u.get("userId")) for u in acl_user}
        group_acl_ids = {str(g.get("groupId")) for g in acl_group}
        user_list = [u for u in user_list if str(u.get("userId")) not in user_acl_ids]
        group_list = [g for g in group_list if str(g.get("groupId")) not in group_acl_ids]

        return {
            "user": {"isEveryone": is_everyone_user, "acl": acl_user, "list": user_list},
            "group": {"isEveryone": is_everyone_group, "acl": acl_group, "list": group_list},
        }

    async def set_acl_list(
        self,
        contents_ids: list[int],
        payload: dict[str, Any],
        user: UserInfo,
        content_type: str = "analysis-tool",
    ) -> bool:
        category = self._as_acl_category(content_type)
        body = dict(payload)
        if contents_ids:
            body["content"] = {"ids": [str(i) for i in contents_ids]}

        headers = self._auth_headers(user)
        return await self.meta_acl.set_acl(category=category, body=body, headers=headers)
