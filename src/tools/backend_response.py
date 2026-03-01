from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class BackendResponse:
    """
    pgv2 BackendResponse 의 Python 버전.
    응답 body(dict)에서 code/errorMsg/errorVars/data 필드를 파싱해 감싼다.
    """

    code: Optional[str] = ""
    errorMsg: Optional[str] = ""
    errorVars: Optional[List[str]] = None
    data: Any = None

    @classmethod
    def from_body(cls, body: Dict[str, Any]) -> "BackendResponse":
        return cls(
            code=body.get("code"),
            errorMsg=body.get("errorMsg"),
            errorVars=body.get("errorVars"),
            data=body.get("data"),
        )

    def is_success(self) -> bool:
        return self.code is None or self.code == "0"

    def is_failed(self) -> bool:
        return not self.is_success()

    def __str__(self) -> str:
        return f"[{self.code}] {self.errorMsg}"

