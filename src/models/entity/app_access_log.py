from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.entity.was_user import WasUser


class AppAccessLog(Base):
    """
    pgv2 com.mobigen.playground.appaccesslog.entity.AppAccessLog 매핑.
    원본 테이블명: play_ground.app_acs_log
    컬럼:
      - id (bigint, pk, auto increment)
      - anls_app_cd (AppCode 문자열)
      - sub_id (nullable)
      - user_id (WasUser.id 와 조인)
      - acs_dt (접속 시각)
    """

    __tablename__ = "app_acs_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    app_code: Mapped[str] = mapped_column("anls_app_cd", String(255), nullable=False)
    sub_id: Mapped[Optional[str]] = mapped_column("sub_id", String(255), nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(
        "user_id", String(255), ForeignKey("was_user.id"), nullable=True
    )
    access_date: Mapped[datetime] = mapped_column("acs_dt", DateTime, nullable=False)

    user: Mapped[Optional[WasUser]] = relationship("WasUser", backref="access_logs")

