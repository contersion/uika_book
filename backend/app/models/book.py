from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.book_group_membership import book_group_memberships
from app.models.mixins import utcnow


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    encoding: Mapped[str] = mapped_column(String(50), default="utf-8", nullable=False)
    total_words: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_chapters: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    chapter_rule_id: Mapped[int | None] = mapped_column(
        ForeignKey("chapter_rules.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="books")
    chapter_rule: Mapped["ChapterRule | None"] = relationship(back_populates="books")
    chapters: Mapped[list["BookChapter"]] = relationship(
        back_populates="book",
        cascade="all, delete-orphan",
        order_by="BookChapter.chapter_index",
    )
    reading_progresses: Mapped[list["ReadingProgress"]] = relationship(
        back_populates="book",
        cascade="all, delete-orphan",
    )
    groups: Mapped[list["BookGroup"]] = relationship(
        secondary=book_group_memberships,
        back_populates="books",
        order_by="BookGroup.name",
    )

