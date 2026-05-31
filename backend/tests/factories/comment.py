from __future__ import annotations

import factory

from ord_people.models.comment import Comment


class CommentFactory(factory.Factory):
    class Meta:
        model = Comment

    text = factory.Sequence(lambda n: f"comment-text-{n}")
    post_id = 0
    author_id = 0
