import secrets


def generate_object_key(prefix: str, ext: str = "webp") -> str:
    return f"{prefix}/{secrets.token_urlsafe(16)}.{ext}"
