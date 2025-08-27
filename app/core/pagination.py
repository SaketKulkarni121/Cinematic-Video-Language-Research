from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field

T = TypeVar('T')


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=24, ge=1, le=60, description="Items per page")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int


def get_offset(page: int, page_size: int) -> int:
    return (page - 1) * page_size


def get_total_pages(total: int, page_size: int) -> int:
    return (total + page_size - 1) // page_size
