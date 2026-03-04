from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.db.session import get_db
from src.services.graphio_service import GraphioService
from src.tools.graphio_client import GraphioClient
from src.utils.common_response import common_response

router = APIRouter(tags=["Graphio"])


@router.get("/v1/graphio/url")
@common_response
async def get_graphio_url(
) -> str:
    settings = get_settings()
    return settings.url.graphio


@router.post("/v1/graphio/app/list")
async def get_graphio_app_list(
    request: Request,
    body: Dict[str, Any] = Body(default_factory=dict),
    db: AsyncSession = Depends(get_db),
) -> dict:
    settings = get_settings()
    compat = settings.compat if isinstance(settings.compat, dict) else {}
    iris = compat.get("iris", {}) if isinstance(compat, dict) else {}
    server_cfg = iris.get("server", {}) if isinstance(iris, dict) else {}
    base_url = str(server_cfg.get("graphio") or "")
    if not base_url:
        base_url = settings.url.graphio if settings.url and settings.url.graphio else ""
    client = GraphioClient(base_url)
    service = GraphioService(db, client)

    # pgv2 GraphioWebController#getAppList: body를 그대로 서비스로 전달하고 결과를 반환
    return await service.get_app_list(body, request)