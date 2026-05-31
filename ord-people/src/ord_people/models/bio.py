from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ord_people.config.constatns.bio import ABOUT_MAX_LENGTH, URL_MAX_LENGTH
from ord_people.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from ord_people.models.user import User


class Bio(Base, TimestampMixin):
    __tablename__ = "bio"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.pk", ondelete="CASCADE"),
        primary_key=True,
    )
    about: Mapped[str | None] = mapped_column(String(ABOUT_MAX_LENGTH), default=None)
    phone_number: Mapped[str | None] = mapped_column(String(16), default=None)
    email: Mapped[str | None] = mapped_column(String(URL_MAX_LENGTH), default=None)
    vk_link: Mapped[str | None] = mapped_column(String(URL_MAX_LENGTH), default=None)
    max_link: Mapped[str | None] = mapped_column(String(URL_MAX_LENGTH), default=None)

    user: Mapped[User] = relationship(back_populates="bio", lazy="raise")
