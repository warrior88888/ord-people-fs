from __future__ import annotations

import asyncio
import io
import logging

from PIL import Image, UnidentifiedImageError

from ord_people.config.constatns.media import (
    ALLOWED_IMAGE_FORMATS,
    IMAGE_OUTPUT_MAX_SIZE,
    IMAGE_OUTPUT_QUALITY,
)
from ord_people.exceptions import InvalidImageError, UnsupportedImageTypeError

logger = logging.getLogger(__name__)


class PillowImageProcessor:
    def __init__(
        self,
        max_size: tuple[int, int] = IMAGE_OUTPUT_MAX_SIZE,
        quality: int = IMAGE_OUTPUT_QUALITY,
    ) -> None:
        self._max_size = max_size
        self._quality = quality
        logger.debug(
            "image_processor_initialized max_size=%dx%d quality=%d",
            max_size[0],
            max_size[1],
            quality,
        )

    def _process_sync(self, data: bytes) -> bytes:
        try:
            with Image.open(io.BytesIO(data)) as img:
                fmt = img.format
                if fmt not in ALLOWED_IMAGE_FORMATS:
                    logger.warning(
                        "image_unsupported_format format=%s bytes=%d",
                        fmt,
                        len(data),
                    )
                    raise UnsupportedImageTypeError
                original_size = img.size
                img = img.convert("RGB")
                img.thumbnail(self._max_size)
                out = io.BytesIO()
                img.save(out, format="WEBP", quality=self._quality, method=6)
                result = out.getvalue()
            logger.debug(
                "image_processed original=%dx%d output_bytes=%d",
                original_size[0],
                original_size[1],
                len(result),
            )
            return result
        except (UnidentifiedImageError, OSError) as e:
            logger.warning(
                "image_invalid bytes=%d error=%s", len(data), e.__class__.__name__
            )
            raise InvalidImageError from e

    async def to_webp(self, data: bytes) -> bytes:
        return await asyncio.get_running_loop().run_in_executor(
            None, self._process_sync, data
        )
