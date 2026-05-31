from __future__ import annotations

import factory

from ord_people.models.bio import Bio


class BioFactory(factory.Factory):
    class Meta:
        model = Bio

    user_id = 0
    about = "Hi I am someone."
    phone_number = None
    email = None
    vk_link = None
    max_link = None
