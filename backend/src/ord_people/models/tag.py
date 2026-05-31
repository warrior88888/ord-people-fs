from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ord_people.models.base import Base, IntPkMixin, TimestampMixin

if TYPE_CHECKING:
    from ord_people.models.post import Post


post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", ForeignKey("post.pk", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tag.pk", ondelete="CASCADE"), primary_key=True),
)


class Tag(Base, IntPkMixin, TimestampMixin):
    __tablename__ = "tag"

    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    posts: Mapped[list[Post]] = relationship(
        secondary=post_tags,
        back_populates="tags",
        lazy="raise",
    )
