from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class WasUser(Base):
    """
    pgv2 com.mobigen.playground.wasuser.entity.WasUser 의 Python/SQLAlchemy 버전.
    원본은 was.was_user 뷰/서브셀렉트를 매핑하지만, 여기서는 동일한 컬럼 구조만 정의한다.
    """

    __tablename__ = "was_user"
    __table_args__ = {"schema": "was"}  # ← 이게 정식 필드

    userId: Mapped[str] = mapped_column("id", String(255), primary_key=True)
    userName: Mapped[str | None] = mapped_column("name", String(255), nullable=True)
    roleCode: Mapped[str | None] = mapped_column("role_code", String(255), nullable=True)