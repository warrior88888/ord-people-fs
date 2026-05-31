from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ord_people.models.base import Base, TimestampMixin
from ord_people.utils.enums import ReactionType

if TYPE_CHECKING:
    from ord_people.models.post import Post
    from ord_people.models.user import User


class Reaction(Base, TimestampMixin):
    __tablename__ = "reaction"

    post_id: Mapped[int] = mapped_column(
        ForeignKey("post.pk", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.pk", ondelete="CASCADE"), primary_key=True
    )
    reaction: Mapped[ReactionType] = mapped_column(
        Enum(ReactionType, name="reaction_type")
    )

    post: Mapped[Post] = relationship(back_populates="reactions", lazy="raise")
    user: Mapped[User] = relationship(back_populates="reactions", lazy="raise")
