from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.db.session import get_db
from src.dto.response.api_response import ApiResponse
from src.middleware.auth import get_current_user
from src.security.session_manager import UserInfo
from src.utils.common_response import common_response

router = APIRouter()


@router.get("/v1/common/session/user")
@common_response
async def get_common_session_user(
    user: UserInfo = Depends(get_current_user),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data=user.model_dump())


@router.get("/v1/common/config")
@common_response
async def get_common_config() -> ApiResponse[dict]:
    settings = get_settings()
    return ApiResponse(
        result="1",
        data={
            "upload": {
                "maxFileSize": None,
                "maxRequestSize": None,
            },
            "analysisTool": settings.analysisTool.model_dump(),
        },
    )


@router.post("/v1/common/token")
@common_response
async def create_common_token(
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    # TODO: 자격증명 검증 및 토큰 발급 로직 구현
    return ApiResponse(result="1", data={"token": ""})

