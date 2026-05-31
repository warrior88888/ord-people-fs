from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ord_people.config.constatns.user import (
    FIRST_NAME_MAX_LENGTH,
    LAST_NAME_MAX_LENGTH,
    USERNAME_MAX_LENGTH,
)
from ord_people.models.base import Base, IntPkMixin, TimestampMixin

if TYPE_CHECKING:
    from ord_people.models.bio import Bio
    from ord_people.models.comment import Comment
    from ord_people.models.post import Post
    from ord_people.models.reaction import Reaction


class User(Base, IntPkMixin, TimestampMixin):
    __tablename__ = "user"

    username: Mapped[str] = mapped_column(
        String(USERNAME_MAX_LENGTH),
        unique=True,
        index=True,
    )
    hashed_password: Mapped[str]
    first_name: Mapped[str] = mapped_column(String(FIRST_NAME_MAX_LENGTH))
    last_name: Mapped[str] = mapped_column(String(LAST_NAME_MAX_LENGTH))
    avatar_key: Mapped[str | None] = mapped_column(default=None)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    bio: Mapped[Bio | None] = relationship(
        back_populates="user",
        uselist=False,
        lazy="raise",
        cascade="all, delete-orphan",
    )
    posts: Mapped[list[Post]] = relationship(
        back_populates="author",
        lazy="raise",
        cascade="all, delete-orphan",
    )
    comments: Mapped[list[Comment]] = relationship(
        back_populates="author",
        lazy="raise",
        cascade="all, delete-orphan",
    )
    reactions: Mapped[list[Reaction]] = relationship(
        back_populates="user",
        lazy="raise",
        cascade="all, delete-orphan",
    )
