from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.db.session import get_db
from src.dto.response.api_response import ApiResponse
from src.middleware.auth import get_current_user
from src.models.entity.analysis_tool import AnalysisTool
from src.models.entity.analysis_tool_approval import AnalysisToolApproval
from src.security.session_manager import UserInfo
from src.services.analysis_tool_service import AnalysisToolService
from src.services.backup_service import BackupService
from src.tools.container_client import ContainerClient
from src.utils.common_response import common_response

router = APIRouter(tags=["AnalysisTool"])


def _container_client() -> ContainerClient:
    settings = get_settings()
    base_url = settings.url.containerManagement if settings.url and settings.url.containerManagement else ""
    return ContainerClient(base_url=base_url)


def _analysis_service(db: AsyncSession) -> AnalysisToolService:
    return AnalysisToolService(db=db, container_client=_container_client())


def _backup_service(db: AsyncSession) -> BackupService:
    return BackupService(db=db, container_client=_container_client())


@router.get("/v1/analysis-tool/meta/create-info")
@common_response
async def get_analysis_tool_create_meta(
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    data = await _container_client().get_create_info()
    return ApiResponse(result="1", data=data.get("data", data))


@router.get("/v1/analysis-tool/meta/resource")
@common_response
async def get_analysis_tool_meta_resource(
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    data = await _container_client().get_resource_info()
    return ApiResponse(result="1", data=data.get("data", data))


@router.get("/v1/analysis-tool/meta/image")
@common_response
async def get_analysis_tool_meta_image(
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    data = await _container_client().get_create_info()
    return ApiResponse(result="1", data=data.get("data", data))


@router.get("/v1/analysis-tool")
@common_response
async def get_analysis_tool_with_count(
    type: str | None = Query(default=None),
    sort: str | None = Query(default=None),
    filter: str | None = Query(default=None),
    offset: int = Query(default=0),
    size: int = Query(default=20),
    status: str | None = Query(default=None),
    approval: str | None = Query(default=None),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    params = {
        "type": type,
        "sort": sort,
        "filter": filter,
        "offset": offset,
        "size": size,
        "status": status,
        "approval": approval,
    }
    data = await _analysis_service(db).get_tool_list_with_count(user, params=params)
    return ApiResponse(result="1", data=data)


@router.get("/v1/analysis-tool/list")
@common_response
async def get_analysis_tool_list(
    type: str | None = Query(default=None),
    sort: str | None = Query(default=None),
    filter: str | None = Query(default=None),
    offset: int = Query(default=0),
    size: int = Query(default=20),
    status: str | None = Query(default=None),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list]:
    params = {
        "type": type,
        "sort": sort,
        "filter": filter,
        "offset": offset,
        "size": size,
        "status": status,
    }
    data = await _analysis_service(db).get_tool_list_with_count(user, params=params)
    return ApiResponse(result="1", data=data.get("items", []))


@router.get("/v1/analysis-tool/list/waiting")
@common_response
async def get_analysis_tool_waiting_list(
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list]:
    stmt = (
        select(AnalysisTool)
        .join(AnalysisToolApproval, AnalysisTool.approval_id == AnalysisToolApproval.id, isouter=True)
        .where(AnalysisToolApproval.status == "NONE")
        .order_by(AnalysisTool.id.desc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    return ApiResponse(
        result="1",
        data=[{"id": row.id, "name": row.name, "status": row.status} for row in rows],
    )


@router.get("/v1/analysis-tool/{id}/detail")
@common_response
async def get_analysis_tool_detail(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    data = await _analysis_service(db).get_tool_detail(id, user)
    return ApiResponse(result="1", data=data)


@router.get("/v1/analysis-tool/{id}/detail/approval")
@common_response
async def get_analysis_tool_detail_approval(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    tool = await db.get(AnalysisTool, id)
    if tool is None or tool.approval_id is None:
        return ApiResponse(result="1", data={"id": id, "approval": None})
    approval = await db.get(AnalysisToolApproval, tool.approval_id)
    return ApiResponse(
        result="1",
        data={
            "id": id,
            "approval": (
                {
                    "id": approval.id,
                    "type": approval.type,
                    "status": approval.status,
                    "cpu": approval.cpu,
                    "gpu": approval.gpu,
                    "mem": approval.mem,
                    "capacity": approval.capacity,
                    "expireDate": str(approval.expire_date) if approval.expire_date else None,
                    "limit": approval.is_limit,
                }
                if approval
                else None
            ),
        },
    )


@router.post("/v1/analysis-tool/exist-name")
@common_response
async def check_analysis_tool_exist_name(
    body: dict[str, Any] = Body(default_factory=dict),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[bool]:
    exists = await _analysis_service(db).check_exist_name(str(body.get("name") or ""), user)
    return ApiResponse(result="1", data=exists)


@router.post("/v1/analysis-tool/create")
@common_response
async def create_analysis_tool(
    body: dict[str, Any] = Body(default_factory=dict),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    data = await _analysis_service(db).create_tool(body, user)
    return ApiResponse(result="1", data=data)


@router.post("/v1/analysis-tool/{id}/reapplication")
@common_response
async def reapplication_analysis_tool(
    id: int = Path(...),
    body: dict[str, Any] = Body(default_factory=dict),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    data = await _analysis_service(db).get_tool_detail(id, user)
    return ApiResponse(result="1", data={"id": id, "detail": data, "payload": body})


@router.post("/v1/analysis-tool/{id}/change-application-info")
@common_response
async def change_application_info(
    id: int = Path(...),
    body: dict[str, Any] = Body(default_factory=dict),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"id": id, "changed": True, "payload": body})


@router.post("/v1/analysis-tool/{id}/update/expire-date")
@common_response
async def update_tool_expire_date(
    id: int = Path(...),
    body: dict[str, Any] = Body(default_factory=dict),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"id": id, "updated": True, "payload": body})


@router.post("/v1/analysis-tool/{id}/update/remove")
@common_response
async def update_tool_remove(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"id": id, "removed": True})


@router.post("/v1/analysis-tool/{id}/cancel")
@common_response
async def cancel_analysis_tool(
    id: int = Path(...),
    body: dict[str, Any] = Body(default_factory=dict),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"id": id, "cancelled": True, "payload": body})


@router.post("/v1/analysis-tool/{id}/stop")
@common_response
async def stop_analysis_tool(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    data = await _analysis_service(db).stop_tool(id, user)
    return ApiResponse(result="1", data=data)


@router.post("/v1/analysis-tool/{id}/tool-restart")
@common_response
async def restart_analysis_tool(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    data = await _analysis_service(db).restart_tool(id, user)
    return ApiResponse(result="1", data=data)


@router.post("/v1/analysis-tool/{id}/delete")
@common_response
async def delete_analysis_tool(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    data = await _analysis_service(db).delete_tool(id, user)
    return ApiResponse(result="1", data=data)


@router.get("/v1/analysis-tool/management/status")
@common_response
async def get_management_status(
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    data = await _analysis_service(db).get_management_status(user)
    return ApiResponse(result="1", data=data)


@router.post("/v1/analysis-tool/management/{id}/approve/create")
@common_response
async def approve_create(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"id": id, "approved": True, "type": "create"})


@router.post("/v1/analysis-tool/management/{id}/approve/resource")
@common_response
async def approve_resource(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"id": id, "approved": True, "type": "resource"})


@router.post("/v1/analysis-tool/management/{id}/approve/expire-date")
@common_response
async def approve_expire_date(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"id": id, "approved": True, "type": "expire-date"})


@router.get("/v1/analysis-tool-preview/{id}/tool-url")
@common_response
async def get_tool_url(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    tool = await db.get(AnalysisTool, id)
    return ApiResponse(result="1", data={"url": tool.container_id if tool else ""})


@router.post("/v1/analysis-tool-preview/{id}/update/access-date")
@common_response
async def update_access_date(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[bool]:
    tool = await db.get(AnalysisTool, id)
    if tool is None:
        return ApiResponse(result="1", data=False)
    from datetime import datetime

    tool.access_date = datetime.utcnow()
    await db.commit()
    return ApiResponse(result="1", data=True)


@router.post("/v1/analysis-tool-preview/{id}/file/list")
@common_response
async def get_file_list_in_tool(
    id: int = Path(...),
    body: dict[str, Any] = Body(default_factory=dict),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list]:
    files = body.get("files")
    if not isinstance(files, list):
        files = []
    return ApiResponse(result="1", data=files)


@router.post("/v1/analysis-tool-preview/{id}/file/import")
@common_response
async def import_file_to_tool(
    id: int = Path(...),
    body: dict[str, Any] = Body(default_factory=dict),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"imported": True, "id": id, "payload": body})


@router.post("/v1/analysis-tool-preview/{id}/file/export")
@common_response
async def export_file_from_tool(
    id: int = Path(...),
    body: dict[str, Any] = Body(default_factory=dict),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"exported": True, "id": id, "payload": body})


@router.get("/v1/analysis-tool/backup/list")
@common_response
async def get_backup_list(
    isShare: bool | None = Query(default=None),
    imageId: str | None = Query(default=None),
    userId: str | None = Query(default=None),
    query: str | None = Query(default=None),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list]:
    params = {"isShare": isShare, "imageId": imageId, "userId": userId, "query": query}
    data = await _backup_service(db).get_backup_list(user, params=params)
    return ApiResponse(result="1", data=data)


@router.get("/v1/analysis-tool/{id}/backup/status")
@common_response
async def get_backup_status(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    data = await _backup_service(db).get_backup_status(id, user)
    return ApiResponse(result="1", data=data)


@router.post("/v1/analysis-tool/backup/exist-name")
@common_response
async def check_backup_exist_name(
    body: dict[str, Any] = Body(default_factory=dict),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[bool]:
    exists = await _backup_service(db).check_backup_exist_name(body, user)
    return ApiResponse(result="1", data=exists)


@router.post("/v1/analysis-tool/{id}/backup")
@common_response
async def backup_tool(
    id: int = Path(...),
    body: dict[str, Any] = Body(default_factory=dict),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    data = await _backup_service(db).backup_tool(id, user, payload=body)
    return ApiResponse(result="1", data=data)


@router.post("/v1/analysis-tool/backup/{backupId}/update")
@common_response
async def update_backup(
    backupId: int = Path(...),
    body: dict[str, Any] = Body(default_factory=dict),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    data = await _backup_service(db).update_backup(backupId, user, payload=body)
    return ApiResponse(result="1", data=data)


@router.post("/v1/analysis-tool/backup/{backupId}/delete")
@common_response
async def delete_backup(
    backupId: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    data = await _backup_service(db).delete_backup(backupId, user)
    return ApiResponse(result="1", data=data)
