from typing import final

from pydantic import BaseModel, PostgresDsn, SecretStr, computed_field

from ord_people.config.fields import PortInt


@final
class PostgresConfig(BaseModel):
    host: str = "localhost"
    db: str = "ord"
    user: str = "postgres"
    password: SecretStr
    port: PortInt = 5432
    pool_size: int = 10
    max_overflow: int = 20

    @computed_field
    @property
    def url(self) -> PostgresDsn:
        """
        Constructs the PostgreSQL database URL.

        Returns:
            PostgresDsn: The constructed database URL.
        """
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.user,
            password=self.password.get_secret_value(),
            host=self.host,
            port=self.port,
            path=self.db,
        )
