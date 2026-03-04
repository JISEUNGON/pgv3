from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.middleware.auth import get_current_user
from src.security.session_manager import UserInfo
from src.services.file_node_service import FileNodeService
from src.utils.common_response import common_response

router = APIRouter(tags=["FileNode"])


@router.get("/v1/file-node")
@common_response
async def get_file_nodes(
    shared: bool | None = Query(default=None),
    sort: str | None = Query(default=None),
    filter: str | None = Query(default=None),
    offset: int = Query(default=0),
    existAcl: bool = Query(default=False),
    type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    sensitive: bool | None = Query(default=None),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = FileNodeService(db)
    return await service.get_file_node_list_with_count(
        user,
        params={
            "shared": shared,
            "sort": sort,
            "filter": filter,
            "offset": offset,
            "size": 20,
            "existAcl": existAcl,
            "type": type,
            "status": status,
            "sensitive": sensitive,
        },
    )


@router.post("/v1/file-node/{id}/rename")
@common_response
async def rename_file_node(
    id: str = Path(...),
    body: dict[str, Any] = Body(default_factory=dict),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> bool:
    service = FileNodeService(db)
    return await service.rename_file_node(id, new_name=str(body.get("name") or ""), user=user)


@router.post("/v1/file-node/exist-name")
@common_response
async def check_exist_file_node_name(
    body: dict[str, Any] = Body(default_factory=dict),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> bool:
    service = FileNodeService(db)
    node_id = body.get("id")
    return await service.get_exist_file_node_name(name=str(body.get("name") or ""), node_id=node_id, user=user)


@router.post("/v1/file-node/exist-name/multi")
@common_response
async def check_exist_file_node_name_multi(
    body: dict[str, Any] = Body(default_factory=dict),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = FileNodeService(db)
    name_list = body.get("nameList")
    if not isinstance(name_list, list):
        name_list = []
    return await service.get_map_file_node_new_name_multi(names=[str(v) for v in name_list], user=user)


@router.post("/v1/file-node/api/update/file-object")
@common_response
async def update_file_object(
    body: dict[str, Any] = Body(default_factory=dict),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> bool:
    service = FileNodeService(db)
    return await service.update_file_object(payload=body, user=user)
