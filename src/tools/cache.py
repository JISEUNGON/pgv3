from __future__ import annotations

from typing import Optional

import redis

from src.core.config import RedisSettings


class CacheClient:
    """
    Redis 기반 캐시/세션 저장소 스켈레톤.
    """

    def __init__(self, settings: RedisSettings) -> None:
        self._client = redis.Redis(host=settings.host, port=settings.port, db=settings.db)

    def set(self, key: str, value: str, expire_seconds: int | None = None) -> None:
        self._client.set(key, value, ex=expire_seconds)

    def get(self, key: str) -> Optional[str]:
        v = self._client.get(key)
        return v.decode("utf-8") if v is not None else None

    def delete(self, key: str) -> None:
        self._client.delete(key)

