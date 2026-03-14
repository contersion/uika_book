from datetime import datetime

from pydantic import Field

from app.schemas.common import ORMModel


class BookChapterBase(ORMModel):
    chapter_index: int = Field(ge=0)
    chapter_title: str = Field(min_length=1, max_length=255)
    start_offset: int = Field(ge=0)
    end_offset: int = Field(ge=0)


class BookChapterSummary(BookChapterBase):
    pass


class BookChapterCreate(BookChapterBase):
    book_id: int


class BookChapterRead(BookChapterBase):
    id: int
    book_id: int
    created_at: datetime


class BookChapterContent(ORMModel):
    book_id: int
    chapter_index: int
    chapter_title: str
    start_offset: int
    end_offset: int
    content: str
