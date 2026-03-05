from __future__ import annotations

import inspect
from functools import wraps
from typing import Any, Callable, Coroutine, TypeVar, get_type_hints

from fastapi import Response, status
from fastapi.responses import JSONResponse

from src.dto.response.api_response import ApiResponse

T = TypeVar("T")


def success(data: Any) -> ApiResponse[Any]:
    return ApiResponse(result="1", errorCode=None, errorMessage=None, data=data)


def failure(error_code: str, message: str) -> ApiResponse[Any]:
    return ApiResponse(result="0", errorCode=error_code, errorMessage=message, data=None)


def _normalize_result_value(payload: Any) -> Any:
    """
    응답 payload 어디에 있든 key가 'result' 인 항목이 int면 str로 변환한다.
    외부 연동 응답(예: {"result": 1})을 그대로 전달하는 경우를 보정하기 위함.
    """
    if isinstance(payload, dict):
        normalized: dict[Any, Any] = {}
        for key, value in payload.items():
            if key == "result" and isinstance(value, int):
                normalized[key] = str(value)
            else:
                normalized[key] = _normalize_result_value(value)
        return normalized
    if isinstance(payload, list):
        return [_normalize_result_value(v) for v in payload]
    return payload


def to_api_response(api_response: ApiResponse[Any], status_code: int = status.HTTP_200_OK) -> Response:
    return JSONResponse(
        status_code=status_code,
        content=_normalize_result_value(api_response.model_dump()),
    )


def common_response(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Coroutine[Any, Any, Response]]:
    # Preserve the original endpoint signature with resolved annotations so
    # FastAPI can correctly detect special params like Request/Response.
    original_sig = inspect.signature(func)
    type_hints = get_type_hints(func, globalns=func.__globals__, localns=None, include_extras=True)
    resolved_params = []
    for p in original_sig.parameters.values():
        if p.name in type_hints:
            resolved_params.append(p.replace(annotation=type_hints[p.name]))
        else:
            resolved_params.append(p)
    resolved_return = type_hints.get("return", original_sig.return_annotation)
    resolved_sig = original_sig.replace(parameters=resolved_params, return_annotation=resolved_return)

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Response:
        result = await func(*args, **kwargs)
        if isinstance(result, ApiResponse):
            api_resp = result
        else:
            api_resp = success(result)
        return to_api_response(api_resp)

    wrapper.__signature__ = resolved_sig
    return wrapper
