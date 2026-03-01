from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    result: str = Field(..., description='"1" for success, "0" for failure')
    errorCode: Optional[str] = None
    errorMessage: Optional[str] = None
    data: Optional[T] = None

