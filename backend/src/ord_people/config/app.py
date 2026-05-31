from typing import final

from pydantic import BaseModel, PositiveInt, SecretStr, computed_field


@final
class AppConfig(BaseModel):
    debug: bool = False
    secret_key: SecretStr = SecretStr("change-me-in-production")
    session_ttl: PositiveInt = 86400
    domain: str = "localhost"
    admin_path: str = "admin"
    behind_proxy: bool = True
    root_path: str = ""
    forwarded_allow_ips: str = "*"
    cookie_secure: bool = True
    container_name: str = "ord_people"
    origin_domain: str = "localhost"

    @computed_field
    @property
    def allowed_hosts(self) -> list[str]:
        return [self.domain, self.container_name, "127.0.0.1", "localhost"]

    @computed_field
    @property
    def cors_origins(self) -> list[str]:
        if self.debug:
            return [
                "http://localhost:3000",
                "http://localhost:8080",
            ]
        return [
            f"https://{self.origin_domain}",
            f"https://www.{self.origin_domain}",
        ]
