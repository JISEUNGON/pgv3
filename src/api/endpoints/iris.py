from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.dto.response.api_response import ApiResponse
from src.middleware.auth import get_current_user
from src.security.session_manager import UserInfo
from src.services.iris_service import IrisService
from src.utils.common_response import common_response

router = APIRouter(tags=["IRIS"])


@router.get("/api/status")
async def iris_status() -> dict[str, bool]:
    return {"status": True}


@router.get("/api/route")
async def iris_route(
    locale: str = Query(default="ko"),
    db: AsyncSession = Depends(get_db),
):
    service = IrisService(db)
    return await service.get_route(locale)


@router.post("/api/event")
async def iris_event() -> str:
    return "success"