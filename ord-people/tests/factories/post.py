from __future__ import annotations

import factory

from ord_people.models.post import Post
from ord_people.utils.enums import PostCategory


class PostFactory(factory.Factory):
    class Meta:
        model = Post

    name = factory.Sequence(lambda n: f"Post {n}")
    description = "An interesting description with enough length."
    category = PostCategory.STORY
    author_id = 0
