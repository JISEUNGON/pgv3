from __future__ import annotations

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.dto.response.api_response import ApiResponse
from src.middleware.auth import get_current_user
from src.security.session_manager import UserInfo
from src.utils.common_response import common_response

router = APIRouter()


@router.get("/v1/analysis-tool/meta/create-info")
@common_response
async def get_analysis_tool_create_meta(
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={})


@router.get("/v1/analysis-tool/meta/resource")
@common_response
async def get_analysis_tool_meta_resource(
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={})


@router.get("/v1/analysis-tool/meta/image")
@common_response
async def get_analysis_tool_meta_image(
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={})


@router.get("/v1/analysis-tool")
@common_response
async def get_analysis_tool_with_count(
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"items": [], "total": 0})


@router.get("/v1/analysis-tool/list")
@common_response
async def get_analysis_tool_list(
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list]:
    return ApiResponse(result="1", data=[])


@router.get("/v1/analysis-tool/list/waiting")
@common_response
async def get_analysis_tool_waiting_list(
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list]:
    return ApiResponse(result="1", data=[])


@router.get("/v1/analysis-tool/{id}/detail")
@common_response
async def get_analysis_tool_detail(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"id": id})


@router.get("/v1/analysis-tool/{id}/detail/approval")
@common_response
async def get_analysis_tool_detail_approval(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"id": id})


@router.post("/v1/analysis-tool/exist-name")
@common_response
async def check_analysis_tool_exist_name(
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[bool]:
    return ApiResponse(result="1", data=False)


@router.post("/v1/analysis-tool/create")
@common_response
async def create_analysis_tool(
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"created": False})


@router.post("/v1/analysis-tool/{id}/reapplication")
@common_response
async def reapplication_analysis_tool(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"id": id})


@router.post("/v1/analysis-tool/{id}/change-application-info")
@common_response
async def change_application_info(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"id": id})


@router.post("/v1/analysis-tool/{id}/update/expire-date")
@common_response
async def update_tool_expire_date(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"id": id})


@router.post("/v1/analysis-tool/{id}/update/remove")
@common_response
async def update_tool_remove(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"id": id})


@router.post("/v1/analysis-tool/{id}/cancel")
@common_response
async def cancel_analysis_tool(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"id": id})


@router.post("/v1/analysis-tool/{id}/stop")
@common_response
async def stop_analysis_tool(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"id": id})


@router.post("/v1/analysis-tool/{id}/tool-restart")
@common_response
async def restart_analysis_tool(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"id": id})


@router.post("/v1/analysis-tool/{id}/delete")
@common_response
async def delete_analysis_tool(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"id": id})


@router.get("/v1/analysis-tool/management/status")
@common_response
async def get_management_status(
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={})


@router.post("/v1/analysis-tool/management/{id}/approve/create")
@common_response
async def approve_create(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"id": id})


@router.post("/v1/analysis-tool/management/{id}/approve/resource")
@common_response
async def approve_resource(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"id": id})


@router.post("/v1/analysis-tool/management/{id}/approve/expire-date")
@common_response
async def approve_expire_date(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"id": id})


@router.get("/v1/analysis-tool-preview/{id}/tool-url")
@common_response
async def get_tool_url(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"url": ""})


@router.post("/v1/analysis-tool-preview/{id}/update/access-date")
@common_response
async def update_access_date(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[bool]:
    return ApiResponse(result="1", data=True)


@router.post("/v1/analysis-tool-preview/{id}/file/list")
@common_response
async def get_file_list_in_tool(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list]:
    return ApiResponse(result="1", data=[])


@router.post("/v1/analysis-tool-preview/{id}/file/import")
@common_response
async def import_file_to_tool(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"imported": False})


@router.post("/v1/analysis-tool-preview/{id}/file/export")
@common_response
async def export_file_from_tool(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"exported": False})


@router.get("/v1/analysis-tool/backup/list")
@common_response
async def get_backup_list(
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list]:
    return ApiResponse(result="1", data=[])


@router.get("/v1/analysis-tool/{id}/backup/status")
@common_response
async def get_backup_status(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"id": id})


@router.post("/v1/analysis-tool/backup/exist-name")
@common_response
async def check_backup_exist_name(
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[bool]:
    return ApiResponse(result="1", data=False)


@router.post("/v1/analysis-tool/{id}/backup")
@common_response
async def backup_tool(
    id: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"id": id})


@router.post("/v1/analysis-tool/backup/{backupId}/update")
@common_response
async def update_backup(
    backupId: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"backupId": backupId})


@router.post("/v1/analysis-tool/backup/{backupId}/delete")
@common_response
async def delete_backup(
    backupId: int = Path(...),
    user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    return ApiResponse(result="1", data={"backupId": backupId})

