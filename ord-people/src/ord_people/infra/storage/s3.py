from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Protocol

from aiobotocore.session import get_session

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from ord_people.config.s3 import S3Config

logger = logging.getLogger(__name__)


class S3Client(Protocol):
    async def put_object(self, **kwargs: object) -> object: ...
    async def delete_object(self, **kwargs: object) -> object: ...


class S3FileStorage:
    def __init__(self, config: S3Config) -> None:
        self._config = config
        self._session = get_session()
        logger.debug(
            "s3_storage_initialized bucket=%s endpoint=%s",
            config.bucket_name,
            config.endpoint_url,
        )

    @asynccontextmanager
    async def _client(self) -> AsyncIterator[S3Client]:
        async with self._session.create_client(
            "s3",
            endpoint_url=str(self._config.endpoint_url),
            aws_access_key_id=self._config.access_key,
            aws_secret_access_key=self._config.secret_key.get_secret_value(),
        ) as client:
            yield client

    async def upload(self, key: str, data: bytes, content_type: str) -> None:
        logger.debug(
            "s3_upload_start key=%s bytes=%d content_type=%s",
            key,
            len(data),
            content_type,
        )
        try:
            async with self._client() as client:
                await client.put_object(
                    Bucket=self._config.bucket_name,
                    Key=key,
                    Body=data,
                    ContentType=content_type,
                    ACL="public-read",
                )
        except Exception:
            logger.exception("s3_upload_failed key=%s", key)
            raise
        logger.info("s3_upload_ok key=%s bytes=%d", key, len(data))

    async def delete(self, key: str) -> None:
        try:
            async with self._client() as client:
                await client.delete_object(Bucket=self._config.bucket_name, Key=key)
        except Exception:
            logger.exception("s3_delete_failed key=%s", key)
            raise
        logger.info("s3_delete_ok key=%s", key)

    def public_url(self, key: str | None) -> str | None:
        if not key:
            return None
        base = str(self._config.public_url).rstrip("/")
        return f"{base}/{key}"
