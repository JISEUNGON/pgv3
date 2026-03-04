from __future__ import annotations

import re
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.entity.file_node import FileNode
from src.security.session_manager import UserInfo


class FileNodeService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _parse_node_id(node_id: str | int | None) -> int | None:
        if node_id is None:
            return None
        if isinstance(node_id, int):
            return node_id
        try:
            return int(str(node_id))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _apply_sort(stmt: Select, sort: str | None) -> Select:
        if not sort:
            return stmt.order_by(FileNode.id.desc())

        parts = sort.split(",")
        if len(parts) < 2:
            return stmt.order_by(FileNode.id.desc())

        key, order = parts[0], parts[1]
        col = FileNode.id
        if key in ("type", "fileType"):
            col = FileNode.file_type
        elif key in ("name", "fileNm"):
            col = FileNode.name
        elif key == "createDate":
            col = FileNode.create_date
        elif key == "updateDate":
            col = FileNode.update_date
        elif key == "expireDate":
            col = FileNode.expire_date
        elif key == "size":
            col = FileNode.file_size
        elif key == "isSensitive":
            col = FileNode.sensitive
        return stmt.order_by(col.asc() if order.upper() == "ASC" else col.desc())

    async def get_file_node_list_with_count(self, user: UserInfo, params: dict[str, Any]) -> dict[str, Any]:
        offset = int(params.get("offset", 0) or 0)
        size = int(params.get("size", 20) or 20)
        if size <= 0:
            size = 20

        stmt = select(FileNode)
        filter_text = (params.get("filter") or "").strip()
        if filter_text:
            stmt = stmt.where(FileNode.name.ilike(f"%{filter_text}%"))
        type_text = (params.get("type") or "").strip()
        if type_text:
            type_values = [v.strip() for v in type_text.split(",") if v.strip()]
            # pgv2 file type enum과 완전 매핑은 추후 스키마 정비 후 보완
            int_values: list[int] = []
            for value in type_values:
                try:
                    int_values.append(int(value))
                except ValueError:
                    continue
            if int_values:
                stmt = stmt.where(FileNode.file_type.in_(int_values))
        if params.get("sensitive") is not None:
            stmt = stmt.where(FileNode.sensitive == bool(params.get("sensitive")))

        sorted_stmt = self._apply_sort(stmt, params.get("sort"))
        result = await self.db.execute(sorted_stmt.offset(offset * size).limit(size))
        rows = result.scalars().all()

        total_stmt = select(func.count()).select_from(FileNode)
        if filter_text:
            total_stmt = total_stmt.where(FileNode.name.ilike(f"%{filter_text}%"))
        total = int((await self.db.execute(total_stmt)).scalar_one())

        list_data = []
        for row in rows:
            list_data.append(
                {
                    "id": str(row.id),
                    "type": str(row.file_type) if row.file_type is not None else None,
                    "name": row.name,
                    "status": {"ready": bool(row.file_stts_ready)},
                    "createDate": row.create_date.isoformat() if row.create_date else None,
                    "updateDate": row.update_date.isoformat() if row.update_date else None,
                    "expireDate": row.expire_date.isoformat() if row.expire_date else None,
                    "size": row.file_size,
                    "isSensitive": row.sensitive,
                    "owner": row.owner_id,
                    "ownerName": row.user.userName if row.user else "UNKNOWN",
                    "isShared": False,
                }
            )

        return {"list": list_data, "total": total, "filtered": total}

    async def rename_file_node(self, node_id: str | int, new_name: str, user: UserInfo) -> bool:
        target_name = (new_name or "").strip()
        if not target_name:
            return False

        parsed_id = self._parse_node_id(node_id)
        if parsed_id is None:
            return False
        node = await self.db.get(FileNode, parsed_id)
        if node is None:
            return False

        node.name = target_name
        await self.db.commit()
        return True

    async def get_exist_file_node_name(self, name: str, node_id: str | int | None, user: UserInfo) -> bool:
        target_name = (name or "").strip()
        if not target_name:
            return True

        stmt = select(FileNode).where(FileNode.name == target_name)
        parsed_id = self._parse_node_id(node_id)
        if parsed_id is not None:
            stmt = stmt.where(FileNode.id != parsed_id)
        exists = (await self.db.execute(stmt.limit(1))).scalar_one_or_none()
        return exists is not None

    async def get_map_file_node_new_name_multi(self, names: list[str], user: UserInfo) -> dict[str, str]:
        async def _resolve_name(base_name: str) -> str:
            candidate = base_name
            while await self.get_exist_file_node_name(candidate, None, user):
                dot = candidate.rfind(".")
                if dot > 0:
                    root = candidate[:dot]
                    ext = candidate[dot:]
                    matched = re.search(r"^(.*)\s\((\d+)\)$", root)
                    if matched:
                        n = int(matched.group(2)) + 1
                        candidate = f"{matched.group(1)} ({n}){ext}"
                    else:
                        candidate = f"{root} (1){ext}"
                else:
                    matched = re.search(r"^(.*)\s\((\d+)\)$", candidate)
                    if matched:
                        n = int(matched.group(2)) + 1
                        candidate = f"{matched.group(1)} ({n})"
                    else:
                        candidate = f"{candidate} (1)"
            return candidate

        result: dict[str, str] = {}
        for org_name in names:
            normalized = (org_name or "").strip()
            if not normalized:
                result[org_name] = org_name
                continue
            new_name = await _resolve_name(normalized)
            result[org_name] = new_name
        return result

    async def update_file_object(self, payload: dict[str, Any], user: UserInfo) -> bool:
        from datetime import date

        file_id = payload.get("fileId")
        if file_id is None:
            return False

        node_id = self._parse_node_id(file_id)
        if node_id is None:
            return False

        node = await self.db.get(FileNode, node_id)
        if node is None:
            return False

        file_name = payload.get("fileName")
        if isinstance(file_name, str) and file_name.strip():
            node.name = file_name.strip()
        file_object_id = payload.get("fileObjectId")
        if isinstance(file_object_id, str):
            node.file_object_id = file_object_id
        if "ready" in payload:
            node.file_stts_ready = bool(payload.get("ready"))
        if "fileSize" in payload and payload.get("fileSize") is not None:
            try:
                node.file_size = int(payload.get("fileSize"))
            except (TypeError, ValueError):
                pass
        if "sensitiveYn" in payload:
            node.sensitive = bool(payload.get("sensitiveYn"))
        expry_date = payload.get("expryDate")
        if isinstance(expry_date, str) and expry_date.strip():
            try:
                node.expire_date = date.fromisoformat(expry_date.strip())
            except ValueError:
                pass

        await self.db.commit()