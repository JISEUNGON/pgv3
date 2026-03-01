from __future__ import annotations

from typing import Iterable, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.entity.was_user import WasUser


class WasUserService:
    """
    pgv2 WasUserRepository(findByUserIdIn)를 Python/SQLAlchemy 로 구현한 서비스.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def find_by_user_ids(self, user_ids: Iterable[str]) -> List[WasUser]:
        stmt = select(WasUser).where(WasUser.userId.in_(list(user_ids)))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

