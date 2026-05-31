from __future__ import annotations

import io

import pytest
from PIL import Image

from ord_people.exceptions import InvalidImageError, UnsupportedImageTypeError
from ord_people.infra.media.image_processor import PillowImageProcessor
from tests.helpers.media import garbage_bytes, jpeg_bytes, png_bytes


@pytest.fixture
def processor() -> PillowImageProcessor:
    return PillowImageProcessor(max_size=(64, 64), quality=80)


async def test_png_converted_to_webp(processor):
    out = await processor.to_webp(png_bytes((32, 32)))
    assert out[:4] == b"RIFF"
    assert b"WEBP" in out[:16]


async def test_jpeg_converted(processor):
    out = await processor.to_webp(jpeg_bytes((32, 32)))
    assert out[:4] == b"RIFF"


async def test_garbage_raises(processor):
    with pytest.raises(InvalidImageError):
        await processor.to_webp(garbage_bytes())


async def test_empty_raises(processor):
    with pytest.raises(InvalidImageError):
        await processor.to_webp(b"")


async def test_resize_caps(processor):
    big = png_bytes((200, 200))
    out = await processor.to_webp(big)
    with Image.open(io.BytesIO(out)) as img:
        assert img.size[0] <= 64
        assert img.size[1] <= 64


async def test_unsupported_format_rejected(processor):
    buf = io.BytesIO()
    Image.new("RGB", (8, 8)).save(buf, format="BMP")
    with pytest.raises(UnsupportedImageTypeError):
        await processor.to_webp(buf.getvalue())
