from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.entity.analysis_tool import AnalysisTool
from src.security.session_manager import UserInfo
from src.tools.container_client import ContainerClient


class AnalysisToolService:
    def __init__(self, db: AsyncSession, container_client: ContainerClient) -> None:
        self.db = db
        self.container_client = container_client

    async def check_exist_name(self, name: str, user: UserInfo) -> bool:
        # TODO: 이름 중복 체크 구현
        return False

    async def create_tool(self, payload: dict[str, Any], user: UserInfo) -> dict[str, Any]:
        # TODO: 리소스 검증 + Approval + Tool 생성 + Container 생성
        return {"created": False}

    async def get_tool_list_with_count(self, user: UserInfo, params: dict[str, Any]) -> dict[str, Any]:
        # TODO: 상태/ACL/이미지 조인 목록/카운트 쿼리 구현
        return {"items": [], "total": 0}

    async def get_tool_detail(self, tool_id: int, user: UserInfo) -> dict[str, Any]:
        # TODO: Tool + ACL + 이미지 메타 + 사용자 정보 조합
        return {"id": tool_id}

    async def get_management_status(self, user: UserInfo) -> dict[str, Any]:
        # TODO: 전체/사용 리소스 조회 후 사용률 계산
        return {}

    async def stop_tool(self, tool_id: int, user: UserInfo) -> dict[str, Any]:
        # TODO: Container stop 호출 + 상태 갱신
        return {"id": tool_id}

    async def restart_tool(self, tool_id: int, user: UserInfo) -> dict[str, Any]:
        # TODO: Container restart 호출 + 상태 갱신
        return {"id": tool_id}

    async def delete_tool(self, tool_id: int, user: UserInfo) -> dict[str, Any]:
        # TODO: Tool 삭제 및 필요 시 컨테이너/리소스 정리
        return {"id": tool_id}

