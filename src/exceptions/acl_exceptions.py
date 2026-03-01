from __future__ import annotations

from src.exceptions.base import BaseCustomException


class AclException(BaseCustomException):
    def __init__(self, message: str, http_status: int = 400) -> None:
        super().__init__(error_code="AclException", message=message, http_status=http_status)


class AclNotFound(AclException):
    def __init__(self, contents_id: int) -> None:
        super().__init__(message=f"ACL for contents {contents_id} not found", http_status=404)

