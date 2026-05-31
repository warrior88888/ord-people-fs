import re
from typing import Annotated

from pydantic import AfterValidator, Field

from ord_people.config.constatns.user import (
    FIRST_NAME_MAX_LENGTH,
    FIRST_NAME_MIN_LENGTH,
    LAST_NAME_MAX_LENGTH,
    LAST_NAME_MIN_LENGTH,
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
    USERNAME_PATTERN,
)


def _validate_username(value: str) -> str:
    if not re.match(USERNAME_PATTERN, value):
        raise ValueError(
            f"Username must be {USERNAME_MIN_LENGTH}-{USERNAME_MAX_LENGTH} "
            "characters long, lowercase, start with a letter, end with a "
            "letter or digit, contain only lowercase letters, digits or "
            "hyphens, and cannot contain consecutive hyphens."
        )
    return value


UsernameField = Annotated[
    str,
    Field(
        min_length=USERNAME_MIN_LENGTH,
        max_length=USERNAME_MAX_LENGTH,
        description=(
            "URL-safe handle: lowercase letters, digits and hyphens; "
            "starts with a letter, ends with a letter or digit; "
            "no consecutive hyphens."
        ),
        examples=["john-doe"],
    ),
    AfterValidator(_validate_username),
]

FirstNameField = Annotated[
    str, Field(min_length=FIRST_NAME_MIN_LENGTH, max_length=FIRST_NAME_MAX_LENGTH)
]

LastNameField = Annotated[
    str, Field(min_length=LAST_NAME_MIN_LENGTH, max_length=LAST_NAME_MAX_LENGTH)
]
