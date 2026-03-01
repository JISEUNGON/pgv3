from __future__ import annotations

from src.exceptions.base import BaseCustomException


class FileNodeException(BaseCustomException):
    def __init__(self, message: str, http_status: int = 400) -> None:
        super().__init__(error_code="FileNodeException", message=message, http_status=http_status)


class FileNodeNotFound(FileNodeException):
    def __init__(self, node_id: int) -> None:
        super().__init__(message=f"File node {node_id} not found", http_status=404)

