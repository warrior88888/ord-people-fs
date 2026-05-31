from pydantic import BaseModel, ConfigDict, Field


class TagSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pk: int
    name: str


class TagCreateSchema(BaseModel):
    name: str = Field(min_length=2, max_length=64)
