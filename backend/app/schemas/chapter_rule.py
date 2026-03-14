from datetime import datetime

from pydantic import Field

from app.schemas.common import ORMModel


class ChapterRuleBase(ORMModel):
    rule_name: str = Field(min_length=1, max_length=100)
    regex_pattern: str = Field(min_length=1)
    flags: str = Field(default="", max_length=50)
    description: str | None = None


class ChapterRuleCreate(ChapterRuleBase):
    is_default: bool = False


class ChapterRuleUpdate(ORMModel):
    rule_name: str | None = Field(default=None, min_length=1, max_length=100)
    regex_pattern: str | None = Field(default=None, min_length=1)
    flags: str | None = Field(default=None, max_length=50)
    description: str | None = None
    is_default: bool | None = None


class ChapterRuleRead(ChapterRuleBase):
    id: int
    user_id: int | None = None
    is_builtin: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime
