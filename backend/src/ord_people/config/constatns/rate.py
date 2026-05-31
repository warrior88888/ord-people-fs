from typing import Final

AUTH_LOGIN: Final[tuple[int, int]] = (60, 60)
AUTH_REGISTER: Final[tuple[int, int]] = (30, 60)
AUTH_LOGOUT: Final[tuple[int, int]] = (120, 60)
AUTH_LOGOUT_ALL: Final[tuple[int, int]] = (30, 60)

POST_CREATE: Final[tuple[int, int]] = (60, 60)
POST_UPDATE: Final[tuple[int, int]] = (120, 60)
POST_DELETE: Final[tuple[int, int]] = (60, 60)
POST_PHOTO_UPLOAD: Final[tuple[int, int]] = (30, 60)
POST_PHOTO_DELETE: Final[tuple[int, int]] = (30, 60)

COMMENT_CREATE: Final[tuple[int, int]] = (180, 60)
COMMENT_UPDATE: Final[tuple[int, int]] = (180, 60)
COMMENT_DELETE: Final[tuple[int, int]] = (120, 60)

REACTION_TOGGLE: Final[tuple[int, int]] = (600, 60)

AVATAR_UPLOAD: Final[tuple[int, int]] = (30, 60)
AVATAR_DELETE: Final[tuple[int, int]] = (30, 60)
BIO_UPDATE: Final[tuple[int, int]] = (60, 60)
USER_UPDATE: Final[tuple[int, int]] = (60, 60)
USER_DELETE: Final[tuple[int, int]] = (10, 60)

TAG_CREATE: Final[tuple[int, int]] = (60, 60)
