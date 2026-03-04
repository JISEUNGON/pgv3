from __future__ import annotations

from fastapi import FastAPI

from src.core.config import get_settings
from src.api.endpoints import (
    acl,
    analysis_tool,
    app_access,
    common,
    file_node,
    graphio,
    image_type,
    iris,
)
from src.dto.response.api_response import ApiResponse
from src.exceptions.base import BaseCustomException
from src.utils.common_response import to_api_response


def create_app() -> FastAPI:
    settings = get_settings()
    compat = settings.compat if isinstance(settings.compat, dict) else {}
    server_cfg = compat.get("server", {}) if isinstance(compat, dict) else {}
    context_path = str(server_cfg.get("contextPath") or "").rstrip("/")
    prefix = "" if context_path in ("", "/") else context_path

    app = FastAPI(
        title="Container Management V3",
        version="0.1.0",
    )

    # 라우터 등록: pgv2 context-path(예: /pgv2) 적용
    app.include_router(app_access.router, prefix=prefix)
    app.include_router(file_node.router, prefix=prefix)
    app.include_router(acl.router, prefix=prefix)
    app.include_router(analysis_tool.router, prefix=prefix)
    app.include_router(image_type.router, prefix=prefix)
    app.include_router(graphio.router, prefix=prefix)
    app.include_router(common.router, prefix=prefix)
    app.include_router(iris.router, prefix=prefix)

    register_exception_handlers(app)

    return app


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BaseCustomException)
    async def handle_custom_exception(_, exc: BaseCustomException):
        api_resp = ApiResponse(
            result="0",
            errorCode=exc.error_code,
            errorMessage=exc.message,
            data=None,
        )
        return to_api_response(api_resp, status_code=exc.http_status)

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(_, exc: Exception):
        api_resp = ApiResponse(
            result="0",
            errorCode=exc.__class__.__name__,
            errorMessage=str(exc),
            data=None,
        )
        return to_api_response(api_resp, status_code=500)
