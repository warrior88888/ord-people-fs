from typing import Final

PHONE_PATTERN: Final[str] = r"^\+7\d{10}$"
PHONE_PATTERN_DESCRIPTION: Final[str] = "+7XXXXXXXXXX"

MAX_LINK_PATTERN: Final[str] = r"^https://(?:www\.)?max\.ru/"
VK_LINK_PATTERN: Final[str] = r"^https://(?:www\.)?vk\.(?:com|ru)/"

ABOUT_MAX_LENGTH: Final[int] = 512

URL_MIN_LENGTH: Final[int] = 10
URL_MAX_LENGTH: Final[int] = 256
