"""API-level request/response and error schemas."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    message: str = ""
    errors: list[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: list[str] = Field(default_factory=list)
    detail: Any = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    environment: str
    llm_model: str
