from __future__ import annotations

import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.security.jwt_utils import create_access_token
from src.security.session_manager import UserInfo, is_system_admin_role


class CommonService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.settings = get_settings()

    @staticmethod
    def _convert_datasize(input_value: str | None) -> float:
        if not input_value:
            return -1

        factors = {
            "kb": 10**3,
            "mb": 10**6,
            "gb": 10**9,
            "tb": 10**12,
        }
        matched = re.search(r"(?P<size>[\d\.]+)\s*(?P<unit>\D*)", input_value.strip())
        if not matched:
            return -1

        size = float(matched.group("size"))
        unit = matched.group("unit").strip().lower()
        return size * factors.get(unit, 1.0)

    def _get_file_config(self) -> dict[str, str]:
        compat = self.settings.compat or {}
        spring = compat.get("spring", {}) if isinstance(compat, dict) else {}
        servlet = spring.get("servlet", {}) if isinstance(spring, dict) else {}
        multipart = servlet.get("multipart", {}) if isinstance(servlet, dict) else {}

        max_file_size = str(multipart.get("maxFileSize", "0"))
        max_request_size = str(multipart.get("maxRequestSize", "0"))
        file_size = self._convert_datasize(max_file_size)
        request_size = self._convert_datasize(max_request_size)
        limit_file_size = min(file_size, request_size) if file_size >= 0 and request_size >= 0 else 0

        return {
            "maxFileSize": max_file_size if file_size <= request_size else max_request_size,
            "limitFileSize": str(limit_file_size),
        }

    async def get_session_user(self, user: UserInfo) -> dict[str, Any]:
        role_code = user.role_code or ("ROOT" if user.is_admin else "USER")
        is_system_admin = is_system_admin_role(role_code)

        return {
            "userId": user.id,
            "name": user.name,
            "groupId": user.group_id or (user.groups[0] if user.groups else None),
            "groupName": user.group_name or (user.groups[0] if user.groups else None),
            "roleCode": role_code,
            "isSystemAdmin": is_system_admin,
            "roleName": user.role_name or ("System Admin" if is_system_admin else "User"),
            "email": user.email,
            "phone": user.phone,
        }

    async def get_config(self) -> dict[str, Any]:
        analysis_tool_cfg = self.settings.analysisTool.model_dump()
        common_cfg = self.settings.common.model_dump()
        file_node_cfg = self.settings.fileNode.model_dump()
        option_cfg = self.settings.option.model_dump(exclude_none=True)

        return {
            "file": self._get_file_config(),
            "common": common_cfg,
            "fileNode": file_node_cfg,
            "analysisTool": {
                "defaultCpu": analysis_tool_cfg.get("defaultCpu"),
                "defaultGpu": analysis_tool_cfg.get("defaultGpu"),
                "defaultMem": analysis_tool_cfg.get("defaultMemory"),
                "defaultCapacity": analysis_tool_cfg.get("defaultCapacity"),
                "maxExpireDate": analysis_tool_cfg.get("maxExpireDuration"),
                # pgv2 분석툴 설정 필드 호환
                "imageGTypeInitialCpu": analysis_tool_cfg.get("imageGTypeInitialCpu", 1),
                "imageGTypeInitialMem": analysis_tool_cfg.get("imageGTypeInitialMem", 1024),
            },
            "option": option_cfg,
        }

    async def create_token(self, credentials: dict[str, Any]) -> dict[str, Any]:
        username = str(credentials.get("username") or "").strip()
        if not username:
            username = "anonymous"
        role_code = str(credentials.get("roleCode") or "USER").strip().upper()
        group_id = credentials.get("groupId")
        group_name = credentials.get("groupName")
        groups = [group_id] if group_id else []

        user = UserInfo(
            id=username,
            name=str(credentials.get("name") or username),
            groups=groups,
            is_admin=is_system_admin_role(role_code),
            group_id=group_id,
            group_name=group_name,
            role_code=role_code,
            role_name=credentials.get("roleName"),
            email=credentials.get("email"),
            phone=credentials.get("phone"),
        )
        access_token = create_access_token(user)
        return {"token": access_token}
