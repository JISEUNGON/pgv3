from __future__ import annotations

from fastapi import APIRouter, Depends

from src.dto.response.api_response import ApiResponse
from src.middleware.auth import get_current_user
from src.security.session_manager import UserInfo
from src.utils.common_response import common_response

router = APIRouter()


@router.get("/api/status")
@common_response
async def iris_status() -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"status": True})


@router.get("/api/route")
@common_response
async def iris_route() -> ApiResponse[dict]:
    # TODO: route_{locale}.yml 로딩 로직 포팅
    return ApiResponse(result="1", data={"routes": []})


@router.post("/api/event")
@common_response
async def iris_event(
    user: UserInfo = Depends(get_current_user),
) -> ApiResponse[str]:
    return ApiResponse(result="1", data="success")


@router.get("/api/heartbeat")
@common_response
async def iris_heartbeat(
    user: UserInfo = Depends(get_current_user),
) -> ApiResponse[dict]:
    # TODO: Brick 토큰 검증/갱신 로직 포팅
    return ApiResponse(result="1", data={"alive": True})

