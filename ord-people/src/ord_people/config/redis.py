from typing import final

from pydantic import BaseModel, RedisDsn, SecretStr, computed_field

from ord_people.config.fields import PortInt


@final
class RedisConfig(BaseModel):
    host: str = "localhost"
    port: PortInt = 6379
    password: SecretStr | None = None
    default_db: int = 0

    @computed_field
    @property
    def url(self) -> str:
        return str(
            RedisDsn.build(
                scheme="redis",
                host=self.host,
                port=self.port,
                password=self.password.get_secret_value() if self.password else None,
                path=f"/{self.default_db}",
            )
        )
