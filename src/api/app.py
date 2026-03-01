from __future__ import annotations

from fastapi import FastAPI

from src.api import api_router
from src.api.endpoints import (
    acl,
    analysis_tool,
    app_access,
    common,
    file_node,
    graphio,
    image_type,
    iris,
    time as time_ep,
)
from src.dto.response.api_response import ApiResponse
from src.exceptions.base import BaseCustomException
from src.utils.common_response import to_api_response


def create_app() -> FastAPI:
    app = FastAPI(
        title="Container Management V3",
        version="0.1.0",
    )

    # 라우터 등록: pgv2와 동일한 path 유지
    app.include_router(app_access.router)
    app.include_router(file_node.router)
    app.include_router(acl.router)
    app.include_router(analysis_tool.router)
    app.include_router(image_type.router)
    app.include_router(graphio.router)
    app.include_router(common.router)
    app.include_router(iris.router)
    app.include_router(time_ep.router)

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

