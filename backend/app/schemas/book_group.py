from datetime import datetime

from pydantic import Field

from app.schemas.common import ORMModel


class BookGroupBase(ORMModel):
    name: str = Field(min_length=1, max_length=100)


class BookGroupCreate(BookGroupBase):
    pass


class BookGroupUpdate(ORMModel):
    name: str = Field(min_length=1, max_length=100)


class BookGroupSummary(ORMModel):
    id: int
    name: str


class BookGroupRead(BookGroupSummary):
    book_count: int = 0
    created_at: datetime
    updated_at: datetime


class BookGroupAssignmentUpdate(ORMModel):
    group_ids: list[int]
