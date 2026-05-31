from __future__ import annotations


class FakeStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.deletes: list[str] = []

    async def upload(self, key: str, data: bytes, content_type: str) -> None:
        self.objects[key] = data

    async def delete(self, key: str) -> None:
        self.deletes.append(key)
        self.objects.pop(key, None)

    def public_url(self, key: str | None) -> str | None:
        if not key:
            return None
        return f"https://fake.cdn/{key}"


class FakeImageProcessor:
    def __init__(self) -> None:
        self.calls: int = 0

    async def to_webp(self, data: bytes) -> bytes:
        self.calls += 1
        return data or b"webp-bytes"
