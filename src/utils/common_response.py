from __future__ import annotations

from typing import Any, Callable, Coroutine, TypeVar

from fastapi import Response, status
from fastapi.responses import JSONResponse

from src.dto.response.api_response import ApiResponse

T = TypeVar("T")


def success(data: Any) -> ApiResponse[Any]:
    return ApiResponse(result="1", errorCode=None, errorMessage=None, data=data)


def failure(error_code: str, message: str) -> ApiResponse[Any]:
    return ApiResponse(result="0", errorCode=error_code, errorMessage=message, data=None)


def to_api_response(api_response: ApiResponse[Any], status_code: int = status.HTTP_200_OK) -> Response:
    return JSONResponse(status_code=status_code, content=api_response.model_dump())


def common_response(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Coroutine[Any, Any, Response]]:
    async def wrapper(*args: Any, **kwargs: Any) -> Response:
        result = await func(*args, **kwargs)
        if isinstance(result, ApiResponse):
            api_resp = result
        else:
            api_resp = success(result)
        return to_api_response(api_resp)

    return wrapper

