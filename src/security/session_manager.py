from __future__ import annotations

from pydantic import BaseModel


def is_system_admin_role(role_code: str | None) -> bool:
    if not role_code:
        return False
    return role_code.upper() in {"SUPER", "ROOT"}


class UserInfo(BaseModel):
    # legacy fields used across pgv3
    id: str
    name: str = ""
    groups: list[str] = []
    is_admin: bool = False

    # pgv2 /common/session/user response compatible fields
    group_id: str | None = None
    group_name: str | None = None
    role_code: str | None = None
    role_name: str | None = None
    email: str | None = None
    phone: str | None = None
