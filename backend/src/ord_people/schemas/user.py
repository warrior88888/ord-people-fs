import datetime

from pydantic import BaseModel, ConfigDict

from ord_people.schemas.bio import BioSchema
from ord_people.utils.fields import FirstNameField, LastNameField


class UserLightSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pk: int
    username: str
    first_name: str
    last_name: str
    avatar_url: str | None = None


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pk: int
    username: str
    first_name: str
    last_name: str
    avatar_url: str | None = None
    is_admin: bool
    created_at: datetime.datetime
    bio: BioSchema | None = None


class UserUpdateSchema(BaseModel):
    first_name: FirstNameField | None = None
    last_name: LastNameField | None = None


class AvatarUploadResponse(BaseModel):
    avatar_url: str
