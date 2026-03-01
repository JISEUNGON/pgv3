from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, pk_int


class ImageType(Base):
    __tablename__ = "image_type"

    id: Mapped[int] = pk_int()
    code: Mapped[str] = mapped_column(String(50), nullable=False)

