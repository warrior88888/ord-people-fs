from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from ord_people.config.admin import AdminConfig
from ord_people.config.app import AppConfig
from ord_people.config.auth import AuthConfig
from ord_people.config.log import LoggingConfig
from ord_people.config.postgres import PostgresConfig
from ord_people.config.redis import RedisConfig
from ord_people.config.s3 import S3Config


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=".env",
        env_prefix="ORD__",
        env_nested_delimiter="__",
    )

    admin: AdminConfig
    app: AppConfig = AppConfig()
    auth: AuthConfig
    log: LoggingConfig = LoggingConfig()
    postgres: PostgresConfig
    redis: RedisConfig = RedisConfig()
    s3: S3Config


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # ty: ignore[missing-argument]
