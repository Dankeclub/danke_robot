"""Unified API response envelope and helper functions."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper.

    All endpoints return this envelope:
        {"code": 0, "msg": "ok", "data": {...}}
    """

    code: int = 0
    msg: str = "ok"
    data: T | None = None


def ok(data: Any = None) -> dict[str, Any]:
    """Build a success response dict.

    Usage:
        return ok({"profile": child_profile})
        return ok()  # data is null
    """
    return {"code": 0, "msg": "ok", "data": data}


def error(code: int, msg: str, data: Any = None) -> dict[str, Any]:
    """Build an error response dict.

    Usage:
        return error(404, "phone_not_bound")
    """
    return {"code": code, "msg": msg, "data": data}
