from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.models.entity.analysis_tool import AnalysisTool
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
        stmt = select(AnalysisTool.id).where(AnalysisTool.name == target_name).limit(1)
        return (await self.db.execute(stmt)).scalar_one_or_none() is not None

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
            "expireDay": (row.expire_date - date.today()).days if row.expire_date else 0,
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

    async def create_tool(self, payload: dict[str, Any], user: UserInfo) -> dict[str, Any]:
        name = str(payload.get("name") or "").strip()
        if not name:
            return {"created": False, "error": "name is required"}
        if await self.check_exist_name(name, user):
            return {"created": False, "error": "name already exists"}

        tool = AnalysisTool(
            name=name,
            status="REQUEST",
            description=str(payload.get("desc") or ""),
            image_id=payload.get("imageId"),
            backup_id=payload.get("backupId"),
            cpu=int(payload.get("cpu") or self.settings.analysisTool.defaultCpu),
            gpu=int(payload.get("gpu") or self.settings.analysisTool.defaultGpu),
            mem=int(payload.get("mem") or self.settings.analysisTool.defaultMemory),
            capacity=int(payload.get("capacity") or self.settings.analysisTool.defaultCapacity),
            owner_id=user.id,
            access_date=datetime.utcnow(),
            create_date=datetime.utcnow(),
            update_date=datetime.utcnow(),
        )
        self.db.add(tool)
        await self.db.commit()
        await self.db.refresh(tool)
        return {"created": True, "id": tool.id}

    async def get_tool_list_with_count(self, user: UserInfo, params: dict[str, Any]) -> dict[str, Any]:
        stmt = select(AnalysisTool)
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
        rows = (await self.db.execute(stmt)).scalars().all()

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

    async def get_tool_detail(self, tool_id: int, user: UserInfo) -> dict[str, Any]:
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
        total = self.settings.cluster_resources.model_dump()
        used = {
            "total_cpu_milli": 0,
            "total_memory_bytes": 0,
            "total_gpu": 0,
            "total_capacity": 0,
        }

        try:
            available = await self.container_client.get_available_resource()
            data = available.get("data", {})
            used["total_cpu_milli"] = max(
                total["total_cpu_milli"] - int(data.get("cpu", total["total_cpu_milli"])),
                0,
            )
            used["total_memory_bytes"] = max(
                total["total_memory_bytes"] - int(data.get("mem", total["total_memory_bytes"])),
                0,
            )
            used["total_gpu"] = max(
                total["total_gpu"] - int(data.get("gpu", total["total_gpu"])),
                0,
            )
            used["total_capacity"] = max(
                total["total_capacity"] - int(data.get("capacity", total["total_capacity"])),
                0,
            )
        except Exception:
            # 외부 CM API 가 없으면 설정값 기준으로만 반환
            pass

        def _rate(u: int, t: int) -> float:
            if t <= 0:
                return 0.0
            return round((u / t) * 100, 2)

        return {
            "total": total,
            "used": used,
            "usageRate": {
                "cpu": _rate(used["total_cpu_milli"], total["total_cpu_milli"]),
                "memory": _rate(used["total_memory_bytes"], total["total_memory_bytes"]),
                "gpu": _rate(used["total_gpu"], total["total_gpu"]),
                "capacity": _rate(used["total_capacity"], total["total_capacity"]),
            },
            "maxExpireDate": self._parse_max_expire_date(),
        }

    async def stop_tool(self, tool_id: int, user: UserInfo) -> dict[str, Any]:
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

    async def restart_tool(self, tool_id: int, user: UserInfo) -> dict[str, Any]:
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

    async def delete_tool(self, tool_id: int, user: UserInfo) -> dict[str, Any]:
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
