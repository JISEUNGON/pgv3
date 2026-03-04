from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.dto.request.app_access import AppAccessAddRequest, AppAccessSearchRequest
from src.middleware.auth import get_current_user
from src.security.session_manager import UserInfo
from src.services.app_access_service import AppAccessService
from src.utils.common_response import common_response

router = APIRouter(tags=["AppAccess"])


@router.post("/v1/app-access/add")
@common_response
async def add_app_access_log(
    body: dict[str, Any] = Body(default_factory=dict),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = AppAccessService(db)
    req = AppAccessAddRequest.model_validate(body)
    return await service.add_access_log(req, user)


@router.get("/v1/app-access")
@common_response
async def get_app_access_with_count(
    appCode: str | None = Query(default=None),
    subId: str | None = Query(default=None),
    userId: str | None = Query(default=None),
    userName: str | None = Query(default=None),
    filter: str | None = Query(default=None),
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    date: str | None = Query(default=None),
    sort: str | None = Query(default=None),
    offset: int = Query(default=0),
    size: int = Query(default=20),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = AppAccessService(db)
    search = AppAccessSearchRequest(
        appCode=appCode,
        subId=subId,
        userId=userId,
        userName=userName,
        filter=filter,
        from_=from_,
        to=to,
        date=date,
        sort=sort,
        offset=offset,
        size=size,
    )
    return await service.get_list_and_count(search)


@router.get("/v1/app-access/list")
@common_response
async def get_app_access_list(
    appCode: str | None = Query(default=None),
    subId: str | None = Query(default=None),
    userId: str | None = Query(default=None),
    userName: str | None = Query(default=None),
    filter: str | None = Query(default=None),
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    date: str | None = Query(default=None),
    sort: str | None = Query(default=None),
    offset: int = Query(default=0),
    size: int = Query(default=20),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    service = AppAccessService(db)
    search = AppAccessSearchRequest(
        appCode=appCode,
        subId=subId,
        userId=userId,
        userName=userName,
        filter=filter,
        from_=from_,
        to=to,
        date=date,
        sort=sort,
        offset=offset,
        size=size,
    )
    return await service.get_list(search)
