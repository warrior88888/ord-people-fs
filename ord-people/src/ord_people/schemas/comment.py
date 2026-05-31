import datetime

from pydantic import BaseModel, ConfigDict, Field

from ord_people.config.constatns.comment import TEXT_MAX_LENGTH, TEXT_MIN_LENGTH
from ord_people.schemas.user import UserLightSchema


class CommentCreateSchema(BaseModel):
    text: str = Field(min_length=TEXT_MIN_LENGTH, max_length=TEXT_MAX_LENGTH)


class CommentUpdateSchema(BaseModel):
    text: str = Field(min_length=TEXT_MIN_LENGTH, max_length=TEXT_MAX_LENGTH)


class CommentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pk: int
    text: str
    author: UserLightSchema
    created_at: datetime.datetime
    updated_at: datetime.datetime
