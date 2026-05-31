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


def oversized_bytes(megabytes: int = 12) -> bytes:
    return b"\x00" * (megabytes * 1024 * 1024)


def garbage_bytes() -> bytes:
    return b"not-an-image-at-all"
