from __future__ import annotations

import io

from PIL import Image


def png_bytes(size: tuple[int, int] = (8, 8)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, (128, 128, 200)).save(buf, format="PNG")
    return buf.getvalue()


def jpeg_bytes(size: tuple[int, int] = (8, 8)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, (10, 200, 10)).save(buf, format="JPEG")
    return buf.getvalue()


def jpeg_bytes_with_exif_orientation(
    size: tuple[int, int] = (40, 20), orientation: int = 6
) -> bytes:
    # iPhone portrait shots arrive as landscape pixels + EXIF Orientation=6
    # ("rotate 270 CW on display"). Building this in-test lets us assert that
    # the processor applies the rotation before re-encoding.
    from PIL import Image as _Image

    img = _Image.new("RGB", size, (10, 200, 10))
    exif = img.getexif()
    exif[0x0112] = orientation  # 0x0112 == Orientation tag
    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif.tobytes())
    return buf.getvalue()


def heic_bytes(size: tuple[int, int] = (8, 8)) -> bytes:
    # pillow_heif registers a HEIF encoder in Pillow; use it to produce a
    # blob that mimics what an iPhone uploads.
    from pillow_heif import register_heif_opener

    register_heif_opener()
    buf = io.BytesIO()
    Image.new("RGB", size, (200, 80, 80)).save(buf, format="HEIF")
    return buf.getvalue()


def webp_bytes(size: tuple[int, int] = (8, 8)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, (50, 50, 200)).save(buf, format="WEBP")
    return buf.getvalue()


def gif_bytes(size: tuple[int, int] = (8, 8)) -> bytes:
    buf = io.BytesIO()
    Image.new("P", size, 1).save(buf, format="GIF")
    return buf.getvalue()


def bmp_bytes(size: tuple[int, int] = (8, 8)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, (200, 50, 200)).save(buf, format="BMP")
    return buf.getvalue()


def tiff_bytes(size: tuple[int, int] = (8, 8)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, (50, 200, 50)).save(buf, format="TIFF")
    return buf.getvalue()


def avif_bytes(size: tuple[int, int] = (8, 8)) -> bytes:
    # Some Android share sheets (Pixel 8+, modern Samsung) emit AVIF.
    # Pillow 11.3+ ships a native AVIF reader/writer.
    buf = io.BytesIO()
    Image.new("RGB", size, (200, 200, 50)).save(buf, format="AVIF")
    return buf.getvalue()


def mpo_bytes(size: tuple[int, int] = (8, 8)) -> bytes:
    # iPhone Portrait / HDR JPEGs are actually MPO containers (multi-frame).
    # Pillow opens them as format="MPO". We build a synthetic two-frame MPO
    # so the processor can be exercised against the same content-type tag.
    img1 = Image.new("RGB", size, (10, 200, 10))
    img2 = Image.new("RGB", size, (10, 10, 200))
    buf = io.BytesIO()
    img1.save(buf, format="MPO", save_all=True, append_images=[img2])
    return buf.getvalue()


def oversized_bytes(megabytes: int = 20) -> bytes:
    return b"\x00" * (megabytes * 1024 * 1024)


def garbage_bytes() -> bytes:
    return b"not-an-image-at-all"
