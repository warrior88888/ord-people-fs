from typing import final

from pydantic import BaseModel, SecretStr

from ord_people.utils.fields import FirstNameField, LastNameField, UsernameField


@final
class AdminConfig(BaseModel):
    username: UsernameField
    password: SecretStr
    first_name: FirstNameField
    last_name: LastNameField
