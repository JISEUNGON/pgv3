from __future__ import annotations

from src.exceptions.base import BaseCustomException


class AppAccessException(BaseCustomException):
    def __init__(self, message: str, http_status: int = 400) -> None:
        super().__init__(error_code="AppAccessException", message=message, http_status=http_status)


class InvalidAppCode(AppAccessException):
    def __init__(self, app_code: str) -> None:
        super().__init__(message=f"Invalid appCode: {app_code}", http_status=400)

