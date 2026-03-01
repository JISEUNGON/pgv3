from __future__ import annotations

from datetime import datetime, timezone


class TimeService:
    async def get_server_time(self) -> str:
        return datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    async def get_time_offset(self, client_time_ms: int | None = None) -> int:
        # TODO: 전달된 클라이언트 시각과 서버 시각의 오프셋 계산
        return 0

