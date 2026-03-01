from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from src.dto.response.api_response import ApiResponse
from src.utils.common_response import common_response

router = APIRouter()


@router.get("/service/time/servertime")
@common_response
async def get_server_time() -> ApiResponse[str]:
    now = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    return ApiResponse(result="1", data=now)


@router.get("/service/time/timeoffset")
@common_response
async def get_time_offset() -> ApiResponse[int]:
    # TODO: 클라이언트 전달 시각과의 offset 계산 로직 구현
    return ApiResponse(result="1", data=0)

