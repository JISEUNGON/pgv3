from __future__ import annotations

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, pk_int


class AnalysisToolApproval(Base):
    __tablename__ = "analysis_tool_approval"

    id: Mapped[int] = pk_int()
    tool_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("analysis_tool.id"), nullable=False
    )

    tool = relationship("AnalysisTool", backref="approvals")

