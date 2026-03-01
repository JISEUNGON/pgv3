from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.dto.request.app_access import AppAccessAddRequest, AppAccessSearchRequest
from src.dto.response.app_access import AppAccessListResponse
from src.middleware.auth import get_current_user
from src.security.session_manager import UserInfo
from src.services.app_access_service import AppAccessService
from src.utils.common_response import common_response

router = APIRouter()


@router.post("/v1/app-access/add")
@common_response
async def add_app_access_log(
    req: AppAccessAddRequest,
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = AppAccessService(db)
    return await service.add_access_log(req, user)


@router.get("/v1/app-access")
@common_response
async def get_app_access_with_count(
    search: AppAccessSearchRequest = Depends(),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AppAccessListResponse:
    service = AppAccessService(db)
    result = await service.get_list_and_count(search)
    return AppAccessListResponse(**result)


@router.get("/v1/app-access/list")
@common_response
async def get_app_access_list(
    search: AppAccessSearchRequest = Depends(),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    service = AppAccessService(db)
    return await service.get_list(search)


