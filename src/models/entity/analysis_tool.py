from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, pk_int


class AnalysisTool(Base):
    __tablename__ = "analysis_tool"

    id: Mapped[int] = pk_int()
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # approvals / backups 관계는 별도 엔티티에서 relationship 으로 연결

