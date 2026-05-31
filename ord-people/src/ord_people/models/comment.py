from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ord_people.config.constatns.comment import TEXT_MAX_LENGTH
from ord_people.models.base import Base, IntPkMixin, TimestampMixin

if TYPE_CHECKING:
    from ord_people.models.post import Post
    from ord_people.models.user import User


class Comment(Base, IntPkMixin, TimestampMixin):
    __tablename__ = "comment"

    post_id: Mapped[int] = mapped_column(
        ForeignKey("post.pk", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[int] = mapped_column(
        ForeignKey("user.pk", ondelete="CASCADE"), index=True
    )
    text: Mapped[str] = mapped_column(String(TEXT_MAX_LENGTH))

    post: Mapped[Post] = relationship(back_populates="comments", lazy="raise")
    author: Mapped[User] = relationship(back_populates="comments", lazy="raise")
