from sqlalchemy import Column, ForeignKey, Table, UniqueConstraint

from app.core.database import Base


book_group_memberships = Table(
    "book_group_memberships",
    Base.metadata,
    Column("book_id", ForeignKey("books.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    Column("group_id", ForeignKey("book_groups.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    UniqueConstraint("book_id", "group_id", name="uq_book_group_memberships_book_group"),
)

