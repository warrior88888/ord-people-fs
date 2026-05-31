from __future__ import annotations

import factory

from ord_people.models.reaction import Reaction
from ord_people.utils.enums import ReactionType


class ReactionFactory(factory.Factory):
    class Meta:
        model = Reaction

    reaction = ReactionType.LIKE
    post_id = 0
    user_id = 0
