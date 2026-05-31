from typing import Final

_DAY: Final[int] = 86_400
_HOUR: Final[int] = 3_600

POST_TTL: Final[int] = _DAY
FEED_TTL: Final[int] = _DAY
FEED_VERSION_KEY: Final[str] = "feed:lite:version"

USER_TTL: Final[int] = _DAY
USERS_FEED_TTL: Final[int] = _HOUR
USERS_FEED_VERSION_KEY: Final[str] = "users:feed:lite:version"

TAGS_TTL: Final[int] = _DAY
TAGS_CACHE_KEY: Final[str] = "tags:all"
