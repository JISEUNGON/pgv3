from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Body, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.dto.response.api_response import ApiResponse
from src.middleware.auth import get_current_user
from src.security.session_manager import UserInfo
from src.services.common_service import CommonService
from src.utils.common_response import common_response

router = APIRouter(tags=["Common"])
logger = logging.getLogger(__name__)


@router.get("/v1/common/session/user")
@common_response
async def get_common_session_user(
    request: Request,
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    service = CommonService(db)
    return ApiResponse(result="1", data=await service.get_session_user(user))


@router.get("/v1/common/config")
@common_response
async def get_common_config(
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    service = CommonService(db)
    return ApiResponse(result="1", data=await service.get_config())