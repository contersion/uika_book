from datetime import datetime

from pydantic import Field

from app.schemas.common import ORMModel


class ReadingProgressBase(ORMModel):
    chapter_index: int = Field(default=0, ge=0)
    char_offset: int = Field(default=0, ge=0)
    percent: float = Field(default=0.0, ge=0.0, le=100.0)


class ReadingProgressCreate(ReadingProgressBase):
    user_id: int
    book_id: int


class ReadingProgressUpdate(ReadingProgressBase):
    pass


class ReadingProgressSyncRequest(ReadingProgressBase):
    updated_at: datetime


class ReadingProgressRead(ReadingProgressBase):
    id: int
    user_id: int
    book_id: int
    updated_at: datetime
