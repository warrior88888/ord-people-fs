from typing import final

from pydantic import BaseModel, PositiveInt


@final
class RateConfig(BaseModel):
    limit: PositiveInt = 100
    window: PositiveInt = 60
