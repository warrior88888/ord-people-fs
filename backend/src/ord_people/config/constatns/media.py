from typing import Final

IMAGE_INPUT_MAX_SIZE: Final[int] = 5 * 1024 * 1024

IMAGE_OUTPUT_MAX_SIZE: Final[tuple[int, int]] = (1280, 1280)
IMAGE_OUTPUT_QUALITY: Final[int] = 85

ALLOWED_IMAGE_CONTENT_TYPES: Final[frozenset[str]] = frozenset(
    {"image/jpeg", "image/png", "image/webp", "image/gif"}
)
ALLOWED_IMAGE_FORMATS: Final[frozenset[str]] = frozenset(
    {"JPEG", "PNG", "WEBP", "GIF"}
)
