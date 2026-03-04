from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.db.session import get_db
from src.middleware.auth import get_current_user
from src.security.session_manager import UserInfo
from src.services.acl_service import AclService
from src.tools.meta_acl_client import MetaAclClient
from src.utils.common_response import common_response

router = APIRouter(tags=["ACL"])

def _meta_acl_client() -> MetaAclClient:
    settings = get_settings()
    base_url = settings.url.meta if settings.url and settings.url.meta else ""
    return MetaAclClient(base_url=base_url)


@router.get("/v1/acl")
@common_response
async def get_acl_candidates(
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = AclService(db, _meta_acl_client())
    return await service.get_list_without_acl(user)


@router.get("/v1/acl/file-node/{contentsId}")
@common_response
async def get_file_node_acl(
    contentsId: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = AclService(db, _meta_acl_client())
    return await service.get_acl_list(contentsId, "file-node", user)


@router.get("/v1/acl/analysis-tool/{contentsId}")
@common_response
async def get_analysis_tool_acl(
    contentsId: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = AclService(db, _meta_acl_client())
    return await service.get_acl_list(contentsId, "analysis-tool", user)


@router.post("/v1/acl/file-node/{contentsId}/update")
@common_response
async def update_file_node_acl(
    contentsId: int = Path(...),
    payload: dict[str, Any] = Body(default_factory=dict),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> bool:
    service = AclService(db, _meta_acl_client())
    return await service.set_acl_list([contentsId], payload=payload, user=user, content_type="file-node")


@router.post("/v1/acl/analysis-tool/{contentsId}/update")
@common_response
async def update_analysis_tool_acl(
    contentsId: int = Path(...),
    payload: dict[str, Any] = Body(default_factory=dict),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> bool:
    service = AclService(db, _meta_acl_client())
    return await service.set_acl_list([contentsId], payload=payload, user=user, content_type="analysis-tool")


@router.post("/v1/acl/file-node/update-multi")
@common_response
async def update_file_node_acl_multi(
    payload: dict[str, Any] = Body(default_factory=dict),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> bool:
    service = AclService(db, _meta_acl_client())
    return await service.set_acl_list([], payload=payload, user=user, content_type="file-node")


@router.post("/v1/acl/analysis-tool/update-multi")
@common_response
async def update_analysis_tool_acl_multi(
    payload: dict[str, Any] = Body(default_factory=dict),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> bool:
    service = AclService(db, _meta_acl_client())
    return await service.set_acl_list([], payload=payload, user=user, content_type="analysis-tool")
