from __future__ import annotations

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.middleware.auth import get_current_user
from src.security.session_manager import UserInfo
from src.services.acl_service import AclService
from src.tools.meta_acl_client import MetaAclClient
from src.utils.common_response import common_response

router = APIRouter()


@router.get("/v1/acl")
@common_response
async def get_acl_candidates(
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = AclService(db, MetaAclClient())
    return await service.get_list_without_acl(user)


@router.get("/v1/acl/file-node/{contentsId}")
@common_response
async def get_file_node_acl(
    contentsId: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = AclService(db, MetaAclClient())
    return await service.get_acl_list(contentsId, "file-node", user)


@router.get("/v1/acl/analysis-tool/{contentsId}")
@common_response
async def get_analysis_tool_acl(
    contentsId: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = AclService(db, MetaAclClient())
    return await service.get_acl_list(contentsId, "analysis-tool", user)


@router.post("/v1/acl/file-node/{contentsId}/update")
@common_response
async def update_file_node_acl(
    contentsId: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> bool:
    service = AclService(db, MetaAclClient())
    return await service.set_acl_list([contentsId], payload={}, user=user)


@router.post("/v1/acl/analysis-tool/{contentsId}/update")
@common_response
async def update_analysis_tool_acl(
    contentsId: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> bool:
    service = AclService(db, MetaAclClient())
    return await service.set_acl_list([contentsId], payload={}, user=user)


@router.post("/v1/acl/file-node/update-multi")
@common_response
async def update_file_node_acl_multi(
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> bool:
    service = AclService(db, MetaAclClient())
    return await service.set_acl_list([], payload={}, user=user)


@router.post("/v1/acl/analysis-tool/update-multi")
@common_response
async def update_analysis_tool_acl_multi(
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> bool:
    service = AclService(db, MetaAclClient())
    return await service.set_acl_list([], payload={}, user=user)

