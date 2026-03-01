from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, pk_int


class ImageInfo(Base):
    __tablename__ = "image_info"

    id: Mapped[int] = pk_int()
    name: Mapped[str] = mapped_column(String(255), nullable=False)

