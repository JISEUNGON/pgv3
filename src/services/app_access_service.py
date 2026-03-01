from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.dto.app_code import AppCode
from src.dto.request.app_access import AppAccessAddRequest, AppAccessSearchRequest
from src.models.entity.app_access_log import AppAccessLog
from src.models.entity.was_user import WasUser
from src.security.session_manager import UserInfo


class AppAccessService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def add_access_log(self, req: AppAccessAddRequest, user: UserInfo | None) -> dict[str, Any]:
        access_date = req.accessDate or datetime.now(tz=timezone.utc)
        code = AppCode.find(req.appCode)
        if code is None:
            return {"success": False, "error": f"Invalid appCode: {req.appCode}"}

        log = AppAccessLog(
            app_code=code.value,
            sub_id=None,
            user_id=user.id if user else "UNKNOWN",
            access_date=access_date.replace(tzinfo=None),
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return {"id": log.id}

    def _apply_search_filters(self, stmt: Select, search: AppAccessSearchRequest) -> Select:
        # 문자열 필터: userId, userName, subId
        if search.filter:
            text = search.filter.strip()
            stmt = stmt.where(
                (WasUser.userId.ilike(f"%{text}%"))
                | (WasUser.userName.ilike(f"%{text}%"))
                | (AppAccessLog.sub_id.ilike(f"%{text}%"))
            )

        # appCode: comma-separated codes
        if search.appCode:
            codes = [c.strip() for c in search.appCode.split(",") if c.strip()]
            enum_list = [AppCode.find(c) for c in codes]
            values = [e.value for e in enum_list if e is not None]
            if values:
                stmt = stmt.where(AppAccessLog.app_code.in_(values))

        if search.subId:
            stmt = stmt.where(AppAccessLog.sub_id == search.subId)
        if search.userId:
            stmt = stmt.where(WasUser.userId == search.userId)
        if search.userName:
            stmt = stmt.where(WasUser.userName.ilike(f"%{search.userName.strip()}%"))

        # 기간 필터(from/to/date)
        def _parse_dt(value: str | None) -> datetime | None:
            if not value:
                return None
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            return None

        from_dt = _parse_dt(search.from_)
        to_dt = _parse_dt(search.to)
        if from_dt and to_dt:
            stmt = stmt.where(AppAccessLog.access_date.between(from_dt, to_dt))
        elif from_dt:
            stmt = stmt.where(AppAccessLog.access_date >= from_dt)
        elif to_dt:
            stmt = stmt.where(AppAccessLog.access_date <= to_dt)

        # date만 지정된 경우 (하루 전체)
        if not (from_dt or to_dt) and search.date:
            base = _parse_dt(search.date)
            if base:
                start = datetime(base.year, base.month, base.day, 0, 0, 0)
                end = datetime(base.year, base.month, base.day, 23, 59, 59)
                stmt = stmt.where(AppAccessLog.access_date.between(start, end))

        return stmt

    def _apply_sorting(self, stmt: Select, sort: str | None) -> Select:
        if not sort:
            return stmt.order_by(AppAccessLog.access_date.desc())

        parts = sort.split(",")
        if len(parts) < 2:
            return stmt.order_by(AppAccessLog.access_date.desc())
        key, order = parts[0], parts[1]

        col = AppAccessLog.access_date
        if key == "appCode":
            col = AppAccessLog.app_code
        elif key == "userId":
            col = WasUser.userId
        elif key == "userName":
            col = WasUser.userName

        if order.upper() == "ASC":
            return stmt.order_by(col.asc())
        return stmt.order_by(col.desc())

    async def get_list_and_count(self, search: AppAccessSearchRequest) -> dict[str, Any]:
        offset = max(search.offset, 0)
        size = search.size if search.size > 0 else 20

        base_stmt = (
            select(AppAccessLog, WasUser)
            .outerjoin(WasUser, AppAccessLog.user_id == WasUser.userId)
            .options(joinedload(AppAccessLog.user))
        )
        filtered_stmt = self._apply_search_filters(base_stmt, search)
        sorted_stmt = self._apply_sorting(filtered_stmt, search.sort)
        paged_stmt = sorted_stmt.offset(offset * size).limit(size)

        result = await self.db.execute(paged_stmt)
        rows: List[tuple[AppAccessLog, WasUser | None]] = result.all()

        items: list[dict[str, Any]] = []
        for log, user in rows:
            items.append(
                {
                    "id": log.id,
                    "appCode": log.app_code,
                    "accessDate": log.access_date,
                    "userId": user.userId if user else log.user_id,
                }
            )

        count_stmt = select(func.count()).select_from(AppAccessLog)
        count_stmt = self._apply_search_filters(count_stmt, search)
        total = (await self.db.execute(count_stmt)).scalar_one()

        return {"items": items, "total": total}

    async def get_list(self, search: AppAccessSearchRequest) -> list[dict[str, Any]]:
        result = await self.get_list_and_count(search)
        return result["items"]

