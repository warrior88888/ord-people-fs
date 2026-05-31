from pydantic import BaseModel, Field

from ord_people.utils.fields import FirstNameField, LastNameField, UsernameField


class RegisterSchema(BaseModel):
    username: UsernameField
    password: str = Field(min_length=8, max_length=128)
    first_name: FirstNameField
    last_name: LastNameField


class RegisterResponseSchema(BaseModel):
    user_id: int
    username: str


class LoginSchema(BaseModel):
    username: UsernameField
    password: str = Field(min_length=8, max_length=128)


class SessionInfoSchema(BaseModel):
    user_id: int
    username: str
