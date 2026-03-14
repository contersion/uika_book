from datetime import datetime

from pydantic import Field

from app.schemas.book_chapter import BookChapterSummary
from app.schemas.chapter_rule import ChapterRuleRead
from app.schemas.common import ORMModel


class BookBase(ORMModel):
    title: str = Field(min_length=1, max_length=255)
    author: str | None = Field(default=None, max_length=255)
    description: str | None = None
    encoding: str = Field(default="utf-8", min_length=1, max_length=50)
    total_words: int = Field(default=0, ge=0)
    total_chapters: int = Field(default=0, ge=0)
    chapter_rule_id: int | None = None


class BookCreate(BookBase):
    user_id: int
    file_name: str = Field(min_length=1, max_length=255)
    file_path: str = Field(min_length=1, max_length=500)


class BookUpdate(ORMModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    author: str | None = Field(default=None, max_length=255)
    description: str | None = None
    encoding: str | None = Field(default=None, min_length=1, max_length=50)
    total_words: int | None = Field(default=None, ge=0)
    total_chapters: int | None = Field(default=None, ge=0)
    chapter_rule_id: int | None = None


class BookReparseRequest(ORMModel):
    chapter_rule_id: int = Field(ge=1)


class BookRead(BookBase):
    id: int
    user_id: int
    file_name: str
    file_path: str
    created_at: datetime
    updated_at: datetime


class BookShelfItem(ORMModel):
    id: int
    title: str
    author: str | None = None
    total_chapters: int
    total_words: int
    last_read_at: datetime | None = None
    progress_percent: float | None = None
    created_at: datetime
    updated_at: datetime


class BookDetail(BookRead):
    chapter_rule: ChapterRuleRead | None = None


class BookReparseResponse(ORMModel):
    book_id: int
    chapter_rule_id: int
    total_chapters: int
    chapters: list[BookChapterSummary]
