"""Common reusable schemas (pagination, wrappers)."""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Page(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)


class Paginated(BaseModel, Generic[T]):
    data: list[T]
    meta: dict


class Ok(BaseModel):
    message: str = "ok"
