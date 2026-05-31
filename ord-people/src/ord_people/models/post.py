from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ord_people.config.constatns.post import (
    DESCRIPTION_MAX_LENGTH,
    EXTERNAL_LINK_MAX_LENGTH,
    NAME_MAX_LENGTH,
)
from ord_people.models.base import Base, IntPkMixin, TimestampMixin
from ord_people.models.tag import post_tags
from ord_people.utils.enums import PostCategory

if TYPE_CHECKING:
    from ord_people.models.comment import Comment
    from ord_people.models.reaction import Reaction
    from ord_people.models.tag import Tag
    from ord_people.models.user import User


class Post(Base, IntPkMixin, TimestampMixin):
    __tablename__ = "post"

    name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH), index=True)
    description: Mapped[str] = mapped_column(String(DESCRIPTION_MAX_LENGTH))
    category: Mapped[PostCategory] = mapped_column(
        Enum(PostCategory, name="post_category"),
        default=PostCategory.STORY,
        index=True,
    )
    photo_key: Mapped[str | None] = mapped_column(default=None)
    external_url: Mapped[str | None] = mapped_column(
        String(EXTERNAL_LINK_MAX_LENGTH), default=None
    )

    author_id: Mapped[int] = mapped_column(
        ForeignKey("user.pk", ondelete="CASCADE"), index=True
    )
    author: Mapped[User] = relationship(back_populates="posts", lazy="raise")

    tags: Mapped[list[Tag]] = relationship(
        secondary=post_tags,
        back_populates="posts",
        lazy="raise",
    )
    comments: Mapped[list[Comment]] = relationship(
        back_populates="post",
        lazy="raise",
        cascade="all, delete-orphan",
    )
    reactions: Mapped[list[Reaction]] = relationship(
        back_populates="post",
        lazy="raise",
        cascade="all, delete-orphan",
    )
