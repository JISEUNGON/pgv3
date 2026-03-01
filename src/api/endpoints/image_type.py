from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.dto.response.api_response import ApiResponse
from src.middleware.auth import get_current_user
from src.security.session_manager import UserInfo
from src.utils.common_response import common_response

router = APIRouter(tags=["ImageType"])


@router.get("/v1/image-type")
@common_response
async def get_image_type_list(
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list]:
    return ApiResponse(result="1", data=[])

