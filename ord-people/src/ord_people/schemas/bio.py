import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from ord_people.config.constatns.bio import (
    ABOUT_MAX_LENGTH,
    MAX_LINK_PATTERN,
    PHONE_PATTERN,
    URL_MAX_LENGTH,
    URL_MIN_LENGTH,
    VK_LINK_PATTERN,
)


class BioSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    about: str | None = None
    phone_number: str | None = None
    email: EmailStr | None = None
    vk_link: str | None = None
    max_link: str | None = None


class BioUpdateSchema(BaseModel):
    """Partial bio update. Empty strings for phone/vk/max links are treated as clear."""

    about: str | None = Field(default=None, max_length=ABOUT_MAX_LENGTH)
    phone_number: str | None = Field(
        default=None,
        description="Russian phone in E.164: `+7XXXXXXXXXX`.",
        examples=["+79991234567"],
    )
    email: EmailStr | None = None
    vk_link: str | None = Field(
        default=None,
        min_length=URL_MIN_LENGTH,
        max_length=URL_MAX_LENGTH,
        description="Must start with `https://vk.com/` or `https://vk.ru/`.",
        examples=["https://vk.com/username"],
    )
    max_link: str | None = Field(
        default=None,
        min_length=URL_MIN_LENGTH,
        max_length=URL_MAX_LENGTH,
        description="Must start with `https://max.ru/`.",
        examples=["https://max.ru/username"],
    )

    @field_validator("phone_number")
    @classmethod
    def _phone(cls, v: str | None) -> str | None:
        if v == "":
            return None
        if v is not None and not re.match(PHONE_PATTERN, v):
            raise ValueError("phone must be +7XXXXXXXXXX")
        return v

    @field_validator("vk_link")
    @classmethod
    def _vk(cls, v: str | None) -> str | None:
        if v == "":
            return None
        if v is not None and not re.match(VK_LINK_PATTERN, v):
            raise ValueError(
                "vk_link must start with https://vk.com/ or https://vk.ru/"
            )
        return v

    @field_validator("max_link")
    @classmethod
    def _max(cls, v: str | None) -> str | None:
        if v == "":
            return None
        if v is not None and not re.match(MAX_LINK_PATTERN, v):
            raise ValueError("max_link must start with https://max.ru/")
        return v
