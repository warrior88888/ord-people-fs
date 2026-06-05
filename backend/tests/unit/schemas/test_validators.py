from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from ord_people.schemas.auth import LoginSchema, RegisterSchema
from ord_people.schemas.bio import BioUpdateSchema
from ord_people.schemas.comment import CommentCreateSchema
from ord_people.schemas.pagination import PaginationParams
from ord_people.schemas.post import PostCreateSchema, PostUpdateSchema
from ord_people.schemas.tag import TagCreateSchema
from ord_people.schemas.user import UserUpdateSchema
from ord_people.utils.enums import PostCategory


class TestRegisterSchema:
    def test_happy(self):
        RegisterSchema(
            username="alice-42",
            password="Sup3rSecret!",
            first_name="Alice",
            last_name="Smith",
        )

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("username", "ab"),
            ("username", "-starts"),
            ("username", "1number"),
            ("username", "double--hyphen"),
            ("username", "wow space"),
            ("username", "ok"),
            ("username", "Alice-42"),
            ("username", "ends-"),
            ("username", "has_underscore"),
            ("password", "short1!"),
            ("password", "x" * 200),
            ("first_name", "x"),
            ("first_name", "x" * 50),
            ("last_name", ""),
        ],
    )
    def test_invalid(self, field, value):
        with pytest.raises(ValidationError):
            RegisterSchema(
                **{
                    "username": "alice-42",
                    "password": "Sup3rSecret!",
                    "first_name": "Alice",
                    "last_name": "Smith",
                    field: value,
                }
            )


class TestLoginSchema:
    def test_happy(self):
        LoginSchema(username="alice-42", password="Sup3rSecret!")

    def test_short_password(self):
        with pytest.raises(ValidationError):
            LoginSchema(username="alice-42", password="x")


class TestPostCreateSchema:
    def test_happy(self):
        PostCreateSchema(
            name="Hello world",
            description="Long enough description.",
            category=PostCategory.STORY,
            tag_ids=[1, 2],
        )

    def test_default_tags(self):
        s = PostCreateSchema(
            name="Hello world",
            description="Long enough description.",
        )
        assert s.tag_ids == []
        assert s.category == PostCategory.STORY

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("name", "xx"),
            ("name", "x" * 51),
            ("description", "short"),
            ("description", "x" * 5001),
            ("category", "invalid"),
            ("external_url", "not-a-url"),
        ],
    )
    def test_invalid(self, field, value):
        kwargs: dict[str, Any] = {
            "name": "Hello world",
            "description": "Long enough description.",
            "category": PostCategory.STORY,
            field: value,
        }
        with pytest.raises(ValidationError):
            PostCreateSchema(**kwargs)


class TestPostUpdateSchema:
    def test_all_optional(self):
        PostUpdateSchema()

    def test_partial(self):
        s = PostUpdateSchema(name="new name")
        assert s.description is None

    def test_invalid(self):
        with pytest.raises(ValidationError):
            PostUpdateSchema(name="x")


class TestCommentCreateSchema:
    @pytest.mark.parametrize("text", ["xy", "x" * 100])
    def test_valid(self, text):
        CommentCreateSchema(text=text)

    @pytest.mark.parametrize("text", ["x", "x" * 101, ""])
    def test_invalid(self, text):
        with pytest.raises(ValidationError):
            CommentCreateSchema(text=text)


class TestTagCreateSchema:
    @pytest.mark.parametrize("name", ["ab", "x" * 64])
    def test_valid(self, name):
        TagCreateSchema(name=name)

    @pytest.mark.parametrize("name", ["a", "x" * 65, ""])
    def test_invalid(self, name):
        with pytest.raises(ValidationError):
            TagCreateSchema(name=name)


class TestUserUpdateSchema:
    def test_empty(self):
        s = UserUpdateSchema()
        assert s.first_name is None

    def test_too_short(self):
        with pytest.raises(ValidationError):
            UserUpdateSchema(first_name="x")


class TestBioUpdateSchema:
    @pytest.mark.parametrize("phone", ["+71234567890", "+79991234567"])
    def test_phone_valid(self, phone):
        BioUpdateSchema(phone_number=phone)

    @pytest.mark.parametrize("phone", ["123", "+1 234", "phone", "+712345678", "+712345678901"])
    def test_phone_invalid(self, phone):
        with pytest.raises(ValidationError):
            BioUpdateSchema(phone_number=phone)

    def test_phone_empty_clears(self):
        s = BioUpdateSchema(phone_number="")
        assert s.phone_number is None

    @pytest.mark.parametrize("vk", ["https://vk.com/alice", "https://www.vk.ru/x"])
    def test_vk_valid(self, vk):
        BioUpdateSchema(vk_link=vk)

    @pytest.mark.parametrize("vk", ["http://vk.com/x", "https://evil.com/x"])
    def test_vk_invalid(self, vk):
        with pytest.raises(ValidationError):
            BioUpdateSchema(vk_link=vk)

    def test_email_invalid(self):
        with pytest.raises(ValidationError):
            BioUpdateSchema(email="not-email")

    def test_about_too_long(self):
        with pytest.raises(ValidationError):
            BioUpdateSchema(about="x" * 2001)

    @pytest.mark.parametrize("mlink", ["https://max.ru/alice", "https://www.max.ru/y"])
    def test_max_valid(self, mlink):
        BioUpdateSchema(max_link=mlink)

    def test_max_invalid(self):
        with pytest.raises(ValidationError):
            BioUpdateSchema(max_link="https://evil.ru/")


class TestPagination:
    @pytest.mark.parametrize(("limit", "offset"), [(1, 0), (100, 0), (20, 99999)])
    def test_valid(self, limit, offset):
        PaginationParams(limit=limit, offset=offset)

    @pytest.mark.parametrize(
        ("limit", "offset"),
        [(0, 0), (101, 0), (-1, 0), (10, -1)],
    )
    def test_invalid(self, limit, offset):
        with pytest.raises(ValidationError):
            PaginationParams(limit=limit, offset=offset)
