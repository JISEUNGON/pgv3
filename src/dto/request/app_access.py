from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AppAccessAddRequest(BaseModel):
    appCode: str
    accessDate: datetime | None = None


class AppAccessSearchRequest(BaseModel):
    appCode: str | None = None
    subId: str | None = None
    userId: str | None = None
    userName: str | None = None
    filter: str | None = None
    from_: str | None = Field(default=None, alias="from")
    to: str | None = None
    date: str | None = None
    sort: str | None = None
    offset: int = 0
    size: int = 20

