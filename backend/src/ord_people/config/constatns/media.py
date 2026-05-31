from typing import Final

IMAGE_INPUT_MAX_SIZE: Final[int] = 12 * 1024 * 1024

IMAGE_OUTPUT_MAX_SIZE: Final[tuple[int, int]] = (1280, 1280)
IMAGE_OUTPUT_QUALITY: Final[int] = 85

ALLOWED_IMAGE_CONTENT_TYPES: Final[frozenset[str]] = frozenset(
    # The MIME check is a first-pass filter — Pillow does the real validation.
    # The intent: accept anything a modern phone or share-sheet might attach.
    {
        # Universal
        "image/jpeg",
        "image/jpg",  # non-standard but seen from some Android share sheets
        "image/pjpeg",  # progressive JPEG, legacy alias
        "image/png",
        "image/webp",
        "image/gif",
        # iPhone / Samsung HEIF family
        "image/heic",
        "image/heif",
        "image/heic-sequence",
        "image/heif-sequence",
        # iPhone Portrait / HDR multi-picture JPEGs
        "image/mpo",
        # AV1 still images — newer Android (Pixel 8+), some share sheets
        "image/avif",
        # Less common but harmless and easily re-encoded
        "image/bmp",
        "image/x-bmp",
        "image/x-ms-bmp",
        "image/tiff",
        "image/x-tiff",
    }
)
ALLOWED_IMAGE_FORMATS: Final[frozenset[str]] = frozenset(
    # Pillow + pillow_heif reports both HEIC and HEIF as "HEIF".
    # iPhone Portrait / HDR shots arrive as "image/jpeg" but Pillow reads
    # them as MPO (Multi-Picture Object — JPEG container with extra frames).
    # AVIF: Pillow 11.3+ ships a native AVIF reader.
    {"JPEG", "PNG", "WEBP", "GIF", "HEIF", "MPO", "AVIF", "BMP", "TIFF"}
)
