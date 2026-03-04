from __future__ import annotations

from src.exceptions.base import BaseCustomException


class AnalysisToolException(BaseCustomException):
    def __init__(self, message: str, http_status: int = 400) -> None:
        super().__init__(error_code="AnalysisToolException", message=message, http_status=http_status)


class AnalysisToolNotFound(AnalysisToolException):
    def __init__(self, tool_id: str) -> None:
        super().__init__(message=f"Analysis tool {tool_id} not found", http_status=404)

