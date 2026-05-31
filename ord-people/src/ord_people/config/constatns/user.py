from typing import Final

FIRST_NAME_MIN_LENGTH: Final[int] = 2
FIRST_NAME_MAX_LENGTH: Final[int] = 32

LAST_NAME_MIN_LENGTH: Final[int] = 2
LAST_NAME_MAX_LENGTH: Final[int] = 32

USERNAME_MIN_LENGTH: Final[int] = 5
USERNAME_MAX_LENGTH: Final[int] = 32
USERNAME_PATTERN: Final[str] = r"^(?!.*--)[a-z][a-z0-9-]{3,30}[a-z0-9]$"

DELETED_DISPLAY_FIRST_NAME: Final[str] = "Удаленный"
DELETED_DISPLAY_LAST_NAME: Final[str] = "аккаунт"
