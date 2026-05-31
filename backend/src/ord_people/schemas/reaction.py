from pydantic import BaseModel, ConfigDict

from ord_people.utils.enums import ReactionType


class ReactionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    post_id: int
    user_id: int
    reaction: ReactionType


class ReactionToggleSchema(BaseModel):
    reaction: ReactionType


class ReactionToggleResponse(BaseModel):
    counts: ReactionCountsSchema
    my_reaction: ReactionType | None


class ReactionCountsSchema(BaseModel):
    like: int = 0
    support: int = 0
    inspiring: int = 0
