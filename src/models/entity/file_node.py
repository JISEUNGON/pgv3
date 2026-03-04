from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, pk_int
from src.models.entity.was_user import WasUser


class FileNode(Base):
    __tablename__ = "file_node"

    id: Mapped[int] = pk_int()
    file_object_id: Mapped[str | None] = mapped_column("file_object_id", String(255), nullable=True)
    file_stts_ready: Mapped[bool | None] = mapped_column("file_stts_ready", Boolean, nullable=True)
    file_type: Mapped[int | None] = mapped_column("file_type", Integer, nullable=True)
    name: Mapped[str] = mapped_column("file_nm", String(255), nullable=False)
    parent_id: Mapped[str | None] = mapped_column("parent_id", String(255), nullable=True)
    create_date: Mapped[datetime | None] = mapped_column("crt_dt", DateTime, nullable=True)
    update_date: Mapped[datetime | None] = mapped_column("updt_dt", DateTime, nullable=True)
    expire_date: Mapped[date | None] = mapped_column("expry_date", Date, nullable=True)
    file_size: Mapped[int | None] = mapped_column("file_sz", Integer, nullable=True)
    sensitive: Mapped[bool | None] = mapped_column("sensitive_yn", Boolean, nullable=True)
    owner_id: Mapped[str | None] = mapped_column("ownr_id", String(255), ForeignKey("was.was_user.id"), nullable=True)

    user: Mapped[WasUser | None] = relationship("WasUser", lazy="joined")
