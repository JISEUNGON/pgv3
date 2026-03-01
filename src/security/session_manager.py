from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from pydantic import BaseModel

from src.core.config import get_settings


class UserInfo(BaseModel):
    id: str
    name: str
    groups: list[str] = []
    is_admin: bool = False


class SessionData(BaseModel):
    user: UserInfo
    expires_at: datetime


class SessionManager:
    """
    간단한 인메모리 세션 매니저 스켈레톤.
    실제 운영에서는 Redis 등 외부 저장소로 교체한다.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, SessionData] = {}
        self._settings = get_settings()

    def create_session(self, user: UserInfo) -> str:
        expire_minutes = self._settings.security.accessTokenExpireMinutes
        expires_at = datetime.now(tz=timezone.utc) + timedelta(minutes=expire_minutes)
        session_id = user.id  # TODO: 실제로는 랜덤 토큰 생성
        self._sessions[session_id] = SessionData(user=user, expires_at=expires_at)
        return session_id

    def get_user(self, session_id: str) -> Optional[UserInfo]:
        data = self._sessions.get(session_id)
        if not data:
            return None
        if data.expires_at < datetime.now(tz=timezone.utc):
            self._sessions.pop(session_id, None)
            return None
        return data.user

    def invalidate_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


_session_manager: SessionManager | None = None


def get_session_manager() -> SessionManager:
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager

