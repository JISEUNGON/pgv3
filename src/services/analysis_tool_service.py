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
        offset = int(params.get("offset", 0) or 0)
        size = int(params.get("size", 20) or 20)
        if size <= 0:
            size = 20

        stmt = select(AnalysisTool)
        filter_text = (params.get("filter") or "").strip()
        if filter_text:
            stmt = stmt.where(AnalysisTool.name.ilike(f"%{filter_text}%"))

        sort = params.get("sort") or "id,DESC"
        sort_parts = sort.split(",")
        sort_key = sort_parts[0] if sort_parts else "id"
        sort_order = sort_parts[1].upper() if len(sort_parts) > 1 else "DESC"
        sort_col = AnalysisTool.name if sort_key in ("name", "toolNm") else AnalysisTool.id
        stmt = stmt.order_by(sort_col.asc() if sort_order == "ASC" else sort_col.desc())

        rows = (await self.db.execute(stmt.offset(offset * size).limit(size))).scalars().all()

        total_stmt = select(func.count()).select_from(AnalysisTool)
        if filter_text:
            total_stmt = total_stmt.where(AnalysisTool.name.ilike(f"%{filter_text}%"))
        total = int((await self.db.execute(total_stmt)).scalar_one())

        return {
            "items": [
                {
                    "id": row.id,
                    "name": row.name,
                    "status": row.status,
                    "owner": row.owner_id,
                    "imageId": row.image_id,
                    "cpu": row.cpu,
                    "gpu": row.gpu,
                    "memory": row.mem,
                    "capacity": row.capacity,
                    "expireDate": str(row.expire_date) if row.expire_date else None,
                }
                for row in rows
            ],
            "total": total,
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
