from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import utcnow


class ChapterRule(Base):
    __tablename__ = "chapter_rules"
    __table_args__ = (UniqueConstraint("user_id", "rule_name", name="uq_chapter_rules_user_rule_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True)
    rule_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    regex_pattern: Mapped[str] = mapped_column(Text, nullable=False)
    flags: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    user: Mapped["User | None"] = relationship(back_populates="chapter_rules")
    books: Mapped[list["Book"]] = relationship(back_populates="chapter_rule")
