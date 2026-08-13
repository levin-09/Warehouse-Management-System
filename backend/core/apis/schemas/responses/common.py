"""Common response schemas."""
from typing import Any, Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class MessageResponse(BaseModel):
    """A generic message response."""

    message: str


class ListResponse(BaseModel, Generic[T]):
    """A generic paginated list response."""

    items: List[T]
    total: int
