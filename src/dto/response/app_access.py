from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AppAccessLogRow(BaseModel):
    id: int
    appCode: str
    accessDate: datetime
    userId: str | None = None


class AppAccessListResponse(BaseModel):
    items: list[AppAccessLogRow]
    total: int

