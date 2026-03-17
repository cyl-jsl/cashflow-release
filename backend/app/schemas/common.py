from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    data: T
    meta: dict = {}

    @classmethod
    def of(cls, data: T) -> "SuccessResponse[T]":
        return cls(data=data, meta={"timestamp": datetime.now().isoformat()})


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class Frequency(str, Enum):
    monthly = "monthly"
    biweekly = "biweekly"
    quarterly = "quarterly"
    yearly = "yearly"
    once = "once"
