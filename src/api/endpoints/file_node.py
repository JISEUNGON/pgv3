from __future__ import annotations

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.middleware.auth import get_current_user
from src.security.session_manager import UserInfo
from src.services.file_node_service import FileNodeService
from src.utils.common_response import common_response

router = APIRouter()


@router.get("/v1/file-node")
@common_response
async def get_file_nodes(
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = FileNodeService(db)
    return await service.get_file_node_list_with_count(user, params={})


@router.post("/v1/file-node/{id}/rename")
@common_response
async def rename_file_node(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = FileNodeService(db)
    return await service.rename_file_node(id, new_name="", user=user)


@router.post("/v1/file-node/exist-name")
@common_response
async def check_exist_file_node_name(
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> bool:
    service = FileNodeService(db)
    return await service.get_exist_file_node_name(name="", node_id=None, user=user)


@router.post("/v1/file-node/exist-name/multi")
@common_response
async def check_exist_file_node_name_multi(
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = FileNodeService(db)
    return await service.get_map_file_node_new_name_multi(names=[], user=user)


@router.post("/v1/file-node/api/update/file-object")
@common_response
async def update_file_object(
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = FileNodeService(db)
    return await service.update_file_object(payload={}, user=user)

