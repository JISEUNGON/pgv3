from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, pk_int


class AnalysisToolBackup(Base):
    __tablename__ = "analysis_tool_backup"

    id: Mapped[int] = pk_int()
    tool_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("analysis_tool.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    tool = relationship("AnalysisTool", backref="backups")

