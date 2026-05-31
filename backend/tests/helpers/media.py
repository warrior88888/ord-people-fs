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


def heic_bytes(size: tuple[int, int] = (8, 8)) -> bytes:
    # pillow_heif registers a HEIF encoder in Pillow; use it to produce a
    # blob that mimics what an iPhone uploads.
    from pillow_heif import register_heif_opener

    register_heif_opener()
    buf = io.BytesIO()
    Image.new("RGB", size, (200, 80, 80)).save(buf, format="HEIF")
    return buf.getvalue()


def oversized_bytes(megabytes: int = 20) -> bytes:
    return b"\x00" * (megabytes * 1024 * 1024)


def garbage_bytes() -> bytes:
    return b"not-an-image-at-all"
