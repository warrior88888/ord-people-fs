from typing import final

from pydantic import BaseModel, HttpUrl, SecretStr


@final
class S3Config(BaseModel):
    access_key: str
    secret_key: SecretStr
    endpoint_url: HttpUrl
    bucket_name: str
    public_url: HttpUrl
