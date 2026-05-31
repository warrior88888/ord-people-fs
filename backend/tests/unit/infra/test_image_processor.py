from __future__ import annotations

import io

import pytest
from PIL import Image

from ord_people.exceptions import InvalidImageError, UnsupportedImageTypeError
from ord_people.infra.media.image_processor import PillowImageProcessor
from tests.helpers.media import (
    avif_bytes,
    bmp_bytes,
    garbage_bytes,
    gif_bytes,
    heic_bytes,
    jpeg_bytes,
    jpeg_bytes_with_exif_orientation,
    mpo_bytes,
    png_bytes,
    tiff_bytes,
    webp_bytes,
)


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
    # ICO is a legitimate Pillow-readable format that we deliberately do not
    # accept — Pillow opens it cleanly so we exercise the allowlist branch.
    buf = io.BytesIO()
    Image.new("RGBA", (16, 16)).save(buf, format="ICO")
    with pytest.raises(UnsupportedImageTypeError):
        await processor.to_webp(buf.getvalue())


async def test_heic_from_iphone_converted_to_webp(processor):
    # iPhone photos arrive as HEIC; pillow_heif teaches Pillow to decode them.
    out = await processor.to_webp(heic_bytes((32, 32)))
    assert out[:4] == b"RIFF"
    assert b"WEBP" in out[:16]


async def test_heic_oversized_resize_caps(processor):
    out = await processor.to_webp(heic_bytes((300, 300)))
    with Image.open(io.BytesIO(out)) as img:
        assert img.size[0] <= 64
        assert img.size[1] <= 64


async def test_webp_input_converted(processor):
    # Pixel screenshots / Telegram share-sheet often emit WebP directly.
    out = await processor.to_webp(webp_bytes((32, 32)))
    assert out[:4] == b"RIFF"


async def test_gif_input_converted(processor):
    out = await processor.to_webp(gif_bytes((32, 32)))
    assert out[:4] == b"RIFF"


async def test_bmp_input_converted(processor):
    out = await processor.to_webp(bmp_bytes((32, 32)))
    assert out[:4] == b"RIFF"


async def test_tiff_input_converted(processor):
    out = await processor.to_webp(tiff_bytes((32, 32)))
    assert out[:4] == b"RIFF"


async def test_avif_input_converted(processor):
    # Newer Android (Pixel 8+) and some share sheets emit AVIF.
    out = await processor.to_webp(avif_bytes((32, 32)))
    assert out[:4] == b"RIFF"


async def test_mpo_from_iphone_portrait_converted(processor):
    # iPhone Portrait / HDR shots are sent as image/jpeg but Pillow reads
    # them as MPO. The processor must accept them and emit a single-frame WebP.
    out = await processor.to_webp(mpo_bytes((32, 32)))
    assert out[:4] == b"RIFF"
    assert b"WEBP" in out[:16]


async def test_jpeg_exif_orientation_applied(processor):
    # 40x20 landscape pixels + Orientation=6 (rotate 270 CW) should produce
    # 20x40 portrait output once the rotation is baked into the pixels.
    src = jpeg_bytes_with_exif_orientation(size=(40, 20), orientation=6)
    out = await processor.to_webp(src)
    with Image.open(io.BytesIO(out)) as img:
        assert img.size == (20, 40)
