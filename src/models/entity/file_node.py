from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, pk_int


class FileNode(Base):
    __tablename__ = "file_node"

    id: Mapped[int] = pk_int()
    # TODO: pgv2 file_node 관련 테이블 스키마를 참고해 세부 컬럼 정의
    name: Mapped[str] = mapped_column(String(255), nullable=False)

