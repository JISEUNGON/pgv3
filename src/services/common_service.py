from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.security.jwt_utils import create_access_token
from src.security.session_manager import SessionManager, UserInfo, get_session_manager


class CommonService:
    def __init__(self, db: AsyncSession, session_manager: SessionManager | None = None) -> None:
        self.db = db
        self.session_manager = session_manager or get_session_manager()
        self.settings = get_settings()

    async def get_session_user(self, user: UserInfo) -> dict[str, Any]:
        return user.model_dump()

    async def get_config(self) -> dict[str, Any]:
        return {
            "analysisTool": self.settings.analysisTool.model_dump(),
        }

    async def create_token(self, credentials: dict[str, Any]) -> dict[str, Any]:
        # TODO: 자격증명 검증 로직을 실제 구현으로 교체
        dummy_user = UserInfo(id="dummy", name="dummy")
        access_token = create_access_token(dummy_user)
        return {"token": access_token}

