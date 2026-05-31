from typing import final

from pydantic import BaseModel, PositiveInt


@final
class AuthConfig(BaseModel):
    pepper: str
    argon2_time_cost: PositiveInt = 2
    argon2_memory_cost: PositiveInt = 65536
    session_ttl: PositiveInt = 86400
