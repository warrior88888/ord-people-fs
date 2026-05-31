from __future__ import annotations

import factory

from ord_people.models.tag import Tag


class TagFactory(factory.Factory):
    class Meta:
        model = Tag

    name = factory.Sequence(lambda n: f"tag{n}")
