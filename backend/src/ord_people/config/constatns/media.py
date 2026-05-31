from typing import Final

IMAGE_INPUT_MAX_SIZE: Final[int] = 12 * 1024 * 1024

IMAGE_OUTPUT_MAX_SIZE: Final[tuple[int, int]] = (1280, 1280)
IMAGE_OUTPUT_QUALITY: Final[int] = 85

ALLOWED_IMAGE_CONTENT_TYPES: Final[frozenset[str]] = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
        # iPhone defaults to HEIC; Safari/Telegram sometimes send heif-sequence.
        "image/heic",
        "image/heif",
        "image/heic-sequence",
        "image/heif-sequence",
    }
)
ALLOWED_IMAGE_FORMATS: Final[frozenset[str]] = frozenset(
    # Pillow + pillow_heif reports both HEIC and HEIF as "HEIF".
    {"JPEG", "PNG", "WEBP", "GIF", "HEIF"}
)
