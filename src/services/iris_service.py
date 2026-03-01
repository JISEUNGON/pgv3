from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.security.session_manager import UserInfo


class IrisService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def status(self) -> dict[str, Any]:
        return {"status": True}

    async def get_route(self, locale: str | None = None) -> dict[str, Any]:
        # TODO: route_{locale}.yml 또는 전체 locale 로딩
        return {"routes": []}

    async def event(self, user: UserInfo) -> str:
        return "success"

    async def heartbeat(self, user: UserInfo) -> dict[str, Any]:
        # TODO: Brick token 검증/갱신 및 세션 토큰 갱신
        return {"alive": True}

