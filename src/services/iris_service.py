from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.security.session_manager import UserInfo


class IrisService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.settings = get_settings()

    def _route_file_path(self, locale: str) -> Path:
        # pgv2 classpath:/i18n/route/route_{locale}.yml 대응
        return Path(__file__).resolve().parents[1] / "resources" / "i18n" / "route" / f"route_{locale}.yml"

    def _load_route_by_locale(self, locale: str) -> dict[str, Any]:
        path = self._route_file_path(locale)
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data if isinstance(data, dict) else {}

    def _get_locales(self) -> list[str]:
        # pgv2: properties.iris.route.locales
        compat = self.settings.compat if isinstance(self.settings.compat, dict) else {}
        iris_cfg = compat.get("iris", {}) if isinstance(compat, dict) else {}
        route_cfg = iris_cfg.get("route", {}) if isinstance(iris_cfg, dict) else {}
        locales = route_cfg.get("locales", [])
        if isinstance(locales, list):
            return [str(l) for l in locales if str(l).strip()]
        if isinstance(locales, str):
            return [s.strip() for s in locales.split(",") if s.strip()]
        return ["ko", "en", "zh", "ja"]

    async def status(self) -> dict[str, Any]:
        return {"status": True}

    async def get_route(self, locale: str | None = None) -> dict[str, Any]:
        locale = (locale or "").strip()
        if locale:
            return self._load_route_by_locale(locale)
        # endpoint default 를 locale 단건 반환으로 맞추기 위해 기본 ko를 사용한다.
        return self._load_route_by_locale("ko")

    async def event(self, user: UserInfo) -> str:
        return "success"

    async def heartbeat(self, user: UserInfo) -> dict[str, Any]:
        # TODO: Brick token 검증/갱신 및 세션 토큰 갱신
        return {"alive": True}
