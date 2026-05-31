from typing import TypeVar

from pydantic import BaseModel, Field

M = TypeVar("M")


class PaginationParams(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class PaginatedResult[M](BaseModel):
    items: list[M]
    total: int
    limit: int
    offset: int

    @property
    def has_next(self) -> bool:
        return self.offset + self.limit < self.total
