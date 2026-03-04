from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.core.config import get_settings
from src.models.entity.analysis_tool import AnalysisTool
from src.models.entity.analysis_tool_approval import AnalysisToolApproval
from src.security.session_manager import UserInfo
from src.tools.container_client import ContainerClient


class AnalysisToolService:
    def __init__(self, db: AsyncSession, container_client: ContainerClient) -> None:
        self.db = db
        self.container_client = container_client
        self.settings = get_settings()

    async def check_exist_name(self, name: str, user: UserInfo) -> bool:
        target_name = (name or "").strip()
        if not target_name:
            return True
        stmt = (
            select(AnalysisTool.id)
            .where(AnalysisTool.name == target_name)
            .where(AnalysisTool.owner_id == user.id)
            .limit(1)
        )
        return (await self.db.execute(stmt)).scalar_one_or_none() is not None

    @staticmethod
    def _parse_expire_date(value: Any) -> date | None:
        if value is None:
            return None
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            v = value.strip()
            if not v:
                return None
            return datetime.strptime(v[:10], "%Y-%m-%d").date()
        return None

    @staticmethod
    def _to_int(value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _get_image_type(image_id: str | None) -> str:
        # pgv2와 동일하게 image tag에 gpu 포함 여부로 구분
        if not image_id:
            return "cpu"
        parts = image_id.split(":")
        tag = parts[-1] if len(parts) > 1 else ""
        return "gpu" if "gpu" in tag.lower() else "cpu"

    async def _get_used_resources(self, excluded_id: str | None = None) -> dict[str, int]:
        active_statuses = ("process", "stopped", "error", "running")
        stmt = select(
            func.coalesce(func.sum(AnalysisTool.cpu), 0),
            func.coalesce(func.sum(AnalysisTool.gpu), 0),
            func.coalesce(func.sum(AnalysisTool.mem), 0),
            func.coalesce(func.sum(AnalysisTool.capacity), 0),
        ).where(func.lower(AnalysisTool.status).in_(active_statuses))
        if excluded_id is not None:
            stmt = stmt.where(AnalysisTool.id != excluded_id)
        row = (await self.db.execute(stmt)).one()
        return {
            "cpu": int(row[0] or 0),
            "gpu": int(row[1] or 0),
            "mem": int(row[2] or 0),
            "capacity": int(row[3] or 0),
        }

    async def _validate_resources(
        self,
        cpu: int,
        gpu: int,
        mem: int,
        capacity: int,
        excluded_id: str | None = None,
    ) -> str | None:
        resource_info = await self.container_client.get_resource_info()
        data = resource_info.get("data", {})
        total = data.get("total", {})
        used = await self._get_used_resources(excluded_id=excluded_id)

        requested = {
            "cpu": cpu,
            "gpu": gpu,
            "mem": mem,
            "capacity": capacity,
        }
        over_limit: list[str] = []
        for key, value in requested.items():
            if value <= 0:
                continue
            quota = self._to_int(total.get(key), 0)
            if key == "cpu":
                quota = quota // 1000
            if used.get(key, 0) + value > quota:
                over_limit.append(key.upper())

        if over_limit:
            return "현재 신청 가능한 리소스가 부족합니다.<br /> 부족한 리소스: " + ", ".join(over_limit)
        return None

    @staticmethod
    def _to_iso_date(d: date) -> str:
        return d.isoformat()

    @staticmethod
    def _parse_max_expire_duration(value: str | None) -> tuple[int, str]:
        # pgv2 max-expire-date: 6M / 1y / 30d
        if not value:
            return 6, "M"
        value = value.strip()
        if len(value) < 2:
            return 6, "M"
        unit = value[-1]
        try:
            amount = int(value[:-1])
        except ValueError:
            return 6, "M"
        return amount, unit

    async def get_create_info(self) -> dict[str, Any]:
        # pgv2 AnalysisToolService#getCreateInfo 포팅
        create_info = await self.container_client.get_create_info()
        data = dict(create_info.get("data", create_info))

        images = data.get("images", [])
        cpu_images: list[dict[str, Any]] = []
        gpu_images: list[dict[str, Any]] = []
        for image in images if isinstance(images, list) else []:
            if not isinstance(image, dict):
                continue
            repo = str(image.get("repo", ""))
            tag = str(image.get("tag", ""))
            temp = {
                "id": f"{repo}:{tag}" if repo or tag else str(image.get("id", "")),
                "name": str(image.get("name", "")),
                "repo": repo,
                "tag": tag,
            }
            if "gpu" in tag.lower():
                gpu_images.append(temp)
            else:
                cpu_images.append(temp)
        data["images"] = cpu_images + gpu_images

        amount, unit = self._parse_max_expire_duration(self.settings.analysisTool.maxExpireDuration)
        today = date.today()
        if unit == "y":
            max_expire = today + timedelta(days=365 * amount)
        elif unit == "d":
            max_expire = today + timedelta(days=amount)
        else:
            max_expire = today + timedelta(days=30 * amount)
        data["maxExpireDate"] = self._to_iso_date(max_expire)

        data["defaultCpu"] = self.settings.analysisTool.defaultCpu
        data["defaultGpu"] = self.settings.analysisTool.defaultGpu
        data["defaultMem"] = self.settings.analysisTool.defaultMemory
        data["defaultCapacity"] = self.settings.analysisTool.defaultCapacity
        data["imageGTypeInitialCpu"] = getattr(self.settings.analysisTool, "imageGTypeInitialCpu", 1)
        data["imageGTypeInitialMem"] = getattr(self.settings.analysisTool, "imageGTypeInitialMem", 1024)
        return data

    @staticmethod
    def _to_tool_response(
        row: AnalysisTool,
        user_id: str,
        image_list: list[dict[str, str]],
    ) -> dict[str, Any]:
        image_name = None
        container_type = None
        if row.image_id and image_list:
            found = next((img for img in image_list if img.get("id") == row.image_id), None)
            if found:
                image_name = found.get("name")
                container_type = found.get("containerType")

        return {
            "id": str(row.id),
            "status": row.status,
            "name": row.name,
            "desc": row.description,
            "imageId": row.image_id,
            "imageName": image_name,
            "containerType": container_type,
            "backupId": row.backup_id,
            "cpu": int(row.cpu or 0),
            "gpu": int(row.gpu or 0),
            "memory": int(row.mem or 0),
            "capacity": int(row.capacity or 0),
            "expireDate": row.expire_date.isoformat() if row.expire_date else None,
            "expireDay": (
                (row.expire_date.date() if isinstance(row.expire_date, datetime) else row.expire_date) - date.today()
            ).days
            if row.expire_date
            else 0,
            "owner": row.owner_id,
            "ownerName": row.user.userName if row.user else "UNKNOWN",
            "createDate": row.create_date.strftime("%Y-%m-%d %H:%M:%S") if row.create_date else None,
            "updateDate": row.update_date.strftime("%Y-%m-%d %H:%M:%S") if row.update_date else None,
            "accessDate": row.access_date.strftime("%Y-%m-%d %H:%M:%S") if row.access_date else None,
            "isShared": False if row.owner_id == user_id else False,
            "approvalId": int(row.approval_id or 0),
            "approvalType": row.approval.type if row.approval else None,
            "approvalStatus": row.approval.status if row.approval else None,
            "limit": row.is_limit,
            "containerId": row.container_id,
        }

    async def _get_image_list(self) -> list[dict[str, str]]:
        create_info = await self.container_client.get_create_info()
        data = create_info.get("data", create_info)
        images = data.get("images", []) if isinstance(data, dict) else []
        result: list[dict[str, str]] = []
        for image in images if isinstance(images, list) else []:
            if not isinstance(image, dict):
                continue
            repo = str(image.get("repo", ""))
            tag = str(image.get("tag", ""))
            result.append(
                {
                    "id": f"{repo}:{tag}" if repo or tag else str(image.get("id", "")),
                    "name": str(image.get("name", "")),
                }
            )
        return result

    async def create_tool(self, payload: dict[str, Any], user: UserInfo) -> str | dict[str, Any]:
        name = str(payload.get("name") or "").strip()
        if not name:
            return {"created": False, "error": "name is required"}

        cpu = self._to_int(payload.get("cpu"), self.settings.analysisTool.defaultCpu)
        gpu = self._to_int(payload.get("gpu"), self.settings.analysisTool.defaultGpu)
        mem = self._to_int(payload.get("mem"), self.settings.analysisTool.defaultMemory)
        capacity = self._to_int(payload.get("capacity"), self.settings.analysisTool.defaultCapacity)
        image_id = payload.get("imageId")
        if self._get_image_type(image_id) == "cpu":
            gpu = 0

        validation_error = await self._validate_resources(cpu, gpu, mem, capacity)
        if validation_error:
            return {"result": "0", "errorMessage": validation_error}

        expire_date = self._parse_expire_date(payload.get("expireDate"))
        is_limit = bool(payload.get("limit", False))

        approval = AnalysisToolApproval(
            type="application",
            status="none",
            cpu=cpu,
            gpu=gpu,
            mem=mem,
            capacity=capacity,
            expire_date=expire_date,
            is_limit=is_limit,
        )
        self.db.add(approval)
        await self.db.flush()

        tool_id = str(uuid.uuid4())
        tool = AnalysisTool(
            id=tool_id,
            name=name,
            status="application",
            description=str(payload.get("desc") or ""),
            image_id=image_id,
            backup_id=payload.get("backupId"),
            cpu=cpu,
            gpu=gpu,
            mem=mem,
            capacity=capacity,
            expire_date=expire_date,
            is_limit=is_limit,
            owner_id=user.id,
            create_date=datetime.utcnow(),
            approval_id=approval.id,
        )
        self.db.add(tool)
        await self.db.commit()
        await self.db.refresh(tool)
        return tool.id

    async def reapplication_tool(self, tool_id: str, payload: dict[str, Any], user: UserInfo) -> bool | dict[str, Any]:
        tool = await self.db.get(AnalysisTool, tool_id)
        if tool is None:
            raise Exception("NO TOOL BY ID")

        cpu = self._to_int(payload.get("cpu"), 0)
        gpu = self._to_int(payload.get("gpu"), 0)
        mem = self._to_int(payload.get("mem"), 0)
        capacity = self._to_int(payload.get("capacity"), 0)
        validation_error = await self._validate_resources(cpu, gpu, mem, capacity, excluded_id=tool_id)
        if validation_error:
            return {"result": "0", "errorMessage": validation_error}

        approval = AnalysisToolApproval(
            type="reapplication",
            status="none",
            cpu=cpu,
            gpu=gpu,
            mem=mem,
            capacity=capacity,
            expire_date=self._parse_expire_date(payload.get("expireDate")),
            is_limit=bool(payload.get("limit", False)),
        )
        self.db.add(approval)
        await self.db.flush()

        name = payload.get("name")
        if isinstance(name, str) and name != "":
            tool.name = name
        desc = payload.get("desc")
        if desc is not None:
            tool.description = str(desc)
        tool.approval_id = approval.id
        tool.update_date = datetime.utcnow()

        await self.db.commit()
        return True

    async def get_tool_list_with_count(self, user: UserInfo, params: dict[str, Any]) -> dict[str, Any]:
        stmt = (
            select(AnalysisTool)
            .options(
                joinedload(AnalysisTool.user),
                selectinload(AnalysisTool.approval),
            )
        )
        view_type = (params.get("type") or "").strip().lower()
        if view_type == "owner":
            stmt = stmt.where(AnalysisTool.owner_id == user.id)
        elif view_type == "share":
            stmt = stmt.where(AnalysisTool.owner_id != user.id)
        elif not user.is_admin:
            # pgv2는 ACL 기준으로 내 컨텐츠 + 공유 받은 컨텐츠를 조회한다.
            # 현재 ACL 완전 포팅 전 단계이므로 최소 보수적으로 내 컨텐츠 기준 적용.
            stmt = stmt.where(AnalysisTool.owner_id == user.id)

        filter_text = (params.get("filter") or "").strip()
        if filter_text:
            stmt = stmt.where(
                (AnalysisTool.name.ilike(f"%{filter_text}%"))
                | (AnalysisTool.description.ilike(f"%{filter_text}%"))
                | (AnalysisTool.owner_id.ilike(f"%{filter_text}%"))
            )

        status_text = (params.get("status") or "").strip()
        if status_text:
            statuses = [s.strip() for s in status_text.split(",") if s.strip()]
            if statuses:
                stmt = stmt.where(AnalysisTool.status.in_(statuses))

        approval = (params.get("approval") or "").strip()
        if approval and approval.upper() == "NONE":
            stmt = stmt.where(AnalysisTool.approval.has(status="NONE"))

        sort = params.get("sort") or "id,DESC"
        sort_parts = sort.split(",")
        sort_key = sort_parts[0] if sort_parts else "id"
        sort_order = sort_parts[1].upper() if len(sort_parts) > 1 else "DESC"
        sort_col = AnalysisTool.id
        if sort_key in ("status", "stts"):
            sort_col = AnalysisTool.status
        elif sort_key in ("name", "toolNm"):
            sort_col = AnalysisTool.name
        elif sort_key in ("ownerName", "owner"):
            sort_col = AnalysisTool.owner_id
        elif sort_key in ("accessDate", "ascDt"):
            sort_col = AnalysisTool.access_date
        stmt = stmt.order_by(sort_col.asc() if sort_order == "ASC" else sort_col.desc())

        # pgv2 getAnalysisToolListAndCount 는 offset/limit 미사용(주석 처리)
        result = await self.db.execute(stmt)
        rows = result.unique().scalars().all()

        filtered_stmt = select(func.count()).select_from(AnalysisTool)
        if view_type == "owner":
            filtered_stmt = filtered_stmt.where(AnalysisTool.owner_id == user.id)
        elif view_type == "share":
            filtered_stmt = filtered_stmt.where(AnalysisTool.owner_id != user.id)
        elif not user.is_admin:
            filtered_stmt = filtered_stmt.where(AnalysisTool.owner_id == user.id)
        if filter_text:
            filtered_stmt = filtered_stmt.where(
                (AnalysisTool.name.ilike(f"%{filter_text}%"))
                | (AnalysisTool.description.ilike(f"%{filter_text}%"))
                | (AnalysisTool.owner_id.ilike(f"%{filter_text}%"))
            )
        if status_text:
            statuses = [s.strip() for s in status_text.split(",") if s.strip()]
            if statuses:
                filtered_stmt = filtered_stmt.where(AnalysisTool.status.in_(statuses))
        if approval and approval.upper() == "NONE":
            filtered_stmt = filtered_stmt.where(AnalysisTool.approval.has(status="NONE"))
        filtered = int((await self.db.execute(filtered_stmt)).scalar_one())

        total_stmt = select(func.count()).select_from(AnalysisTool)
        total = int((await self.db.execute(total_stmt)).scalar_one())
        image_list = await self._get_image_list()
        list_data = [self._to_tool_response(row, user.id, image_list) for row in rows]

        return {
            "list": list_data,
            "total": total,
            "filtered": filtered,
        }

    async def get_tool_detail(self, tool_id: str, user: UserInfo) -> dict[str, Any]:
        tool = await self.db.get(AnalysisTool, tool_id)
        if tool is None:
            return {"id": tool_id, "exists": False}
        return {
            "id": tool.id,
            "name": tool.name,
            "status": tool.status,
            "description": tool.description,
            "ownerId": tool.owner_id,
            "imageId": tool.image_id,
            "backupId": tool.backup_id,
            "cpu": tool.cpu,
            "gpu": tool.gpu,
            "mem": tool.mem,
            "capacity": tool.capacity,
            "expireDate": str(tool.expire_date) if tool.expire_date else None,
            "limit": tool.is_limit,
            "containerId": tool.container_id,
            "exists": True,
        }

    async def get_tool_detail_approval(self, tool_id: str, user: UserInfo) -> dict[str, Any]:
        # pgv2 getDetailApproval:
        # 기본 상세정보를 만들고, approval 값이 있으면 신청 리소스로 덮어써서 반환
        tool = await self.db.get(AnalysisTool, tool_id)
        if tool is None:
            return {"id": tool_id, "exists": False}

        approval = await self.db.get(AnalysisToolApproval, tool.approval_id) if tool.approval_id else None
        image_list = await self._get_image_list()
        data = self._to_tool_response(tool, user.id, image_list)

        if approval is not None:
            cpu = int(approval.cpu or 0)
            gpu = int(approval.gpu or 0)
            mem = int(approval.mem or 0)
            capacity = int(approval.capacity or 0)
            if cpu > 0:
                data["cpu"] = cpu
            if gpu > 0:
                data["gpu"] = gpu
            if mem > 0:
                data["memory"] = mem
            if capacity > 0:
                data["capacity"] = capacity

            expire_date = approval.expire_date.isoformat() if approval.expire_date else None
            data["expireDate"] = expire_date
            _exp = approval.expire_date
            _exp_date = _exp.date() if isinstance(_exp, datetime) else _exp
            data["expireDay"] = (_exp_date - date.today()).days if _exp_date else 0
            data["limit"] = approval.is_limit

        return data

    def _parse_max_expire_date(self) -> str:
        value = (self.settings.analysisTool.maxExpireDuration or "6M").strip()
        if len(value) < 2:
            return str(date.today() + timedelta(days=180))

        unit = value[-1].lower()
        try:
            amount = int(value[:-1])
        except ValueError:
            amount = 6
            unit = "m"

        if unit == "y":
            return str(date.today() + timedelta(days=365 * amount))
        if unit == "d":
            return str(date.today() + timedelta(days=amount))
        return str(date.today() + timedelta(days=30 * amount))

    async def get_management_status(self, user: UserInfo) -> dict[str, Any]:
        # pgv2 AnalysisToolService#getManagementStatus 포팅:
        # - container-management /v1/resource-info 응답의 total/used/percent 형태 유지
        # - cpu 는 milli -> core 로 변환해 반환
        resource_info = await self.container_client.get_resource_info()
        data = resource_info.get("data", {})
        total = dict(data.get("total", {}))
        used = dict(data.get("used", {}))

        total_cpu = int(total.get("cpu", 0) or 0)
        total_gpu = int(total.get("gpu", 0) or 0)
        total_mem = int(total.get("mem", 0) or 0)
        total_capacity = int(total.get("capacity", 0) or 0)

        used_cpu = int(used.get("cpu", 0) or 0)
        used_gpu = int(used.get("gpu", 0) or 0)
        used_mem = int(used.get("mem", 0) or 0)
        used_capacity = int(used.get("capacity", 0) or 0)

        total["cpu"] = total_cpu // 1000
        used["cpu"] = used_cpu // 1000

        approval_count_stmt = (
            select(func.count(AnalysisTool.id))
            .select_from(AnalysisTool)
            .join(AnalysisToolApproval, AnalysisTool.approval_id == AnalysisToolApproval.id, isouter=True)
            .where(func.lower(func.coalesce(AnalysisToolApproval.status, "")) == "none")
        )
        request_count = int((await self.db.execute(approval_count_stmt)).scalar_one() or 0)

        return {
            "total": total,
            "used": used,
            "percent": {
                "cpu": -1 if total_cpu == 0 else (used_cpu * 100.0) / total_cpu,
                "gpu": -1 if total_gpu == 0 else (used_gpu * 100.0) / total_gpu,
                "mem": -1 if total_mem == 0 else (used_mem * 100.0) / total_mem,
                "capacity": -1 if total_capacity == 0 else (used_capacity * 100.0) / total_capacity,
            },
            "lastRequestDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "requestCount": request_count,
        }

    async def stop_tool(self, tool_id: str, user: UserInfo) -> dict[str, Any]:
        # pgv2 는 tool.containerId 로 stop 호출한다. 현재 스키마 제약으로 tool_id 를 컨테이너 ID로 사용.
        tool = await self.db.get(AnalysisTool, tool_id)
        container_id = str(tool.container_id) if tool and tool.container_id else str(tool_id)
        try:
            data = await self.container_client.stop_container(container_id)
            if tool is not None:
                tool.status = "STOP"
                tool.update_date = datetime.utcnow()
                await self.db.commit()
            return {"id": tool_id, "stopped": True, "container": data}
        except Exception:
            return {"id": tool_id, "stopped": False}

    async def restart_tool(self, tool_id: str, user: UserInfo) -> dict[str, Any]:
        tool = await self.db.get(AnalysisTool, tool_id)
        container_id = str(tool.container_id) if tool and tool.container_id else str(tool_id)
        try:
            data = await self.container_client.restart_container_with_params(
                container_id=container_id,
                params={},
            )
            if tool is not None:
                tool.status = "PROCESS"
                tool.update_date = datetime.utcnow()
                await self.db.commit()
            return {"id": tool_id, "restarted": True, "container": data}
        except Exception:
            return {"id": tool_id, "restarted": False}

    async def delete_tool(self, tool_id: str, user: UserInfo) -> dict[str, Any]:
        tool = await self.db.get(AnalysisTool, tool_id)
        if tool is None:
            return {"id": tool_id, "deleted": False}

        self.db.delete(tool)
        await self.db.commit()

        container_id = str(tool.container_id) if tool.container_id else str(tool_id)
        try:
            await self.container_client.delete_container(container_id)
        except Exception:
            pass
        return {"id": tool_id, "deleted": True}
