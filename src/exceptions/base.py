from __future__ import annotations

from typing import Optional


class BaseCustomException(Exception):
    def __init__(self, error_code: str, message: str, http_status: int = 400) -> None:
        self.error_code = error_code
        self.message = message
        self.http_status = http_status
        super().__init__(message)


class AuthenticationException(BaseCustomException):
    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(error_code="AuthenticationException", message=message, http_status=401)


class AuthorizationException(BaseCustomException):
    def __init__(self, message: str = "Access denied") -> None:
        super().__init__(error_code="AuthorizationException", message=message, http_status=403)

