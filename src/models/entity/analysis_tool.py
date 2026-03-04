from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, pk_int
from src.models.entity.was_user import WasUser


class AnalysisTool(Base):
    __tablename__ = "analysis_tool"

    id: Mapped[int] = pk_int()
    container_id: Mapped[str | None] = mapped_column("container_id", String(255), nullable=True)
    status: Mapped[str] = mapped_column("stts", String(64), nullable=False, default="REQUEST")
    name: Mapped[str] = mapped_column("tool_nm", String(255), nullable=False)
    description: Mapped[str | None] = mapped_column("description", String(2000), nullable=True)
    image_id: Mapped[str | None] = mapped_column("image_id", String(255), nullable=True)
    backup_id: Mapped[str | None] = mapped_column("backup_id", String(255), nullable=True)
    cpu: Mapped[int | None] = mapped_column("cpu", Integer, nullable=True)
    gpu: Mapped[int | None] = mapped_column("gpu", Integer, nullable=True)
    mem: Mapped[int | None] = mapped_column("mem", Integer, nullable=True)
    capacity: Mapped[int | None] = mapped_column("capacity", Integer, nullable=True)
    expire_date: Mapped[date | None] = mapped_column("expry_dt", Date, nullable=True)
    is_limit: Mapped[bool | None] = mapped_column("limit", Boolean, nullable=True)
    owner_id: Mapped[str | None] = mapped_column("ownr_id", String(255), ForeignKey("was.was_user.id"), nullable=True)
    create_date: Mapped[datetime | None] = mapped_column("crt_dt", DateTime, nullable=True)
    update_date: Mapped[datetime | None] = mapped_column("updt_dt", DateTime, nullable=True)
    access_date: Mapped[datetime | None] = mapped_column("acs_dt", DateTime, nullable=True)
    approval_id: Mapped[int | None] = mapped_column(
        "approval_id",
        Integer,
        ForeignKey("analysis_tool_approval.id"),
        nullable=True,
    )

    user: Mapped[WasUser | None] = relationship("WasUser", lazy="joined")
    approval = relationship("AnalysisToolApproval", back_populates="tool", uselist=False)
