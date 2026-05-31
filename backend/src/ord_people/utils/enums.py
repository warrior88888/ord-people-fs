from enum import StrEnum


class PostCategory(StrEnum):
    STORY = "story"
    EVENT = "event"
    HELP = "help"
    VOLUNTEER = "volunteer"
    NEWS = "news"


class ReactionType(StrEnum):
    LIKE = "like"
    SUPPORT = "support"
    INSPIRING = "inspiring"
