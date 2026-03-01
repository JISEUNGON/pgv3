from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.dto.response.api_response import ApiResponse
from src.middleware.auth import get_current_user
from src.security.session_manager import UserInfo
from src.core.config import get_settings
from src.services.graphio_service import GraphioService
from src.tools.graphio_client import GraphioClient
from src.utils.common_response import common_response

router = APIRouter()


@router.get("/v1/graphio/url")
@common_response
async def get_graphio_url(
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    settings = get_settings()
    base_url = settings.url.graphio if settings.url and settings.url.graphio else ""
    client = GraphioClient(base_url)
    service = GraphioService(db, client)
    return ApiResponse(result="1", data=await service.get_url())


@router.post("/v1/graphio/app/list")
@common_response
async def get_graphio_app_list(
    body: Dict[str, Any],
    authorization: str | None = Header(default=None),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    settings = get_settings()
    base_url = settings.url.graphio if settings.url and settings.url.graphio else ""
    client = GraphioClient(base_url)
    service = GraphioService(db, client)

    access_token = ""
    if authorization and authorization.lower().startswith("bearer "):
        access_token = authorization.split(" ", 1)[1].strip()

    data = await service.get_app_list(body, access_token)
    return ApiResponse(result="1", data=data)

