from pydantic import BaseModel, Field, model_validator


class RuleTestRequest(BaseModel):
    book_id: int | None = Field(default=None, ge=1)
    text: str | None = None
    regex_pattern: str = Field(min_length=1)
    flags: str = Field(default="", max_length=100)

    @model_validator(mode="after")
    def validate_source(self) -> "RuleTestRequest":
        if self.book_id is None and self.text is None:
            raise ValueError("Either book_id or text is required")
        return self


class RuleTestItem(BaseModel):
    text: str
    start: int
    end: int


class RuleTestResponse(BaseModel):
    matched: bool
    count: int
    items: list[RuleTestItem]
