from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, pk_int


class AnalysisToolApproval(Base):
    __tablename__ = "analysis_tool_approval"

    id: Mapped[int] = pk_int()
    type: Mapped[str | None] = mapped_column("type", String(64), nullable=True)
    status: Mapped[str | None] = mapped_column("stts", String(64), nullable=True)
    cpu: Mapped[int | None] = mapped_column("cpu", Integer, nullable=True)
    gpu: Mapped[int | None] = mapped_column("gpu", Integer, nullable=True)
    mem: Mapped[int | None] = mapped_column("mem", Integer, nullable=True)
    capacity: Mapped[int | None] = mapped_column("capacity", Integer, nullable=True)
    expire_date: Mapped[date | None] = mapped_column("expry_dt", Date, nullable=True)
    is_limit: Mapped[bool | None] = mapped_column("limit", Boolean, nullable=True)

    tool = relationship("AnalysisTool", back_populates="approval")
