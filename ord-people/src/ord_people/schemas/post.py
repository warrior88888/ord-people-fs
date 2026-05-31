import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from ord_people.config.constatns.post import (
    DESCRIPTION_MAX_LENGTH,
    DESCRIPTION_MIN_LENGTH,
    NAME_MAX_LENGTH,
    NAME_MIN_LENGTH,
)
from ord_people.schemas.reaction import ReactionCountsSchema
from ord_people.schemas.tag import TagSchema
from ord_people.schemas.user import UserLightSchema
from ord_people.utils.enums import PostCategory, ReactionType


class PostCreateSchema(BaseModel):
    name: str = Field(min_length=NAME_MIN_LENGTH, max_length=NAME_MAX_LENGTH)
    description: str = Field(
        min_length=DESCRIPTION_MIN_LENGTH, max_length=DESCRIPTION_MAX_LENGTH
    )
    category: PostCategory = PostCategory.STORY
    external_url: HttpUrl | None = None
    tag_ids: list[int] = Field(default_factory=list)


class PostUpdateSchema(BaseModel):
    name: str | None = Field(
        default=None, min_length=NAME_MIN_LENGTH, max_length=NAME_MAX_LENGTH
    )
    description: str | None = Field(
        default=None,
        min_length=DESCRIPTION_MIN_LENGTH,
        max_length=DESCRIPTION_MAX_LENGTH,
    )
    category: PostCategory | None = None
    external_url: HttpUrl | None = None
    tag_ids: list[int] | None = None


class PostLightSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pk: int
    name: str
    category: PostCategory
    photo_url: str | None = None
    created_at: datetime.datetime


class PostSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pk: int
    name: str
    description: str
    category: PostCategory
    photo_url: str | None = None
    external_url: str | None = None
    author: UserLightSchema
    tags: list[TagSchema]
    reactions: ReactionCountsSchema
    my_reaction: ReactionType | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class PhotoUploadResponse(BaseModel):
    photo_url: str


class PostFeedFilters(BaseModel):
    category: PostCategory | None = None
    tag_ids: list[int] = Field(default_factory=list)
    date_from: datetime.datetime | None = None
    date_to: datetime.datetime | None = None
