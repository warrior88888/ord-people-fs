from __future__ import annotations

import pytest

from tests.helpers.media import png_bytes

# (method, url-template, requires_auth, ownership_url_template_or_None,
#  json_body, files_factory)
PROTECTED_ENDPOINTS = [
    ("POST", "/api/v1/auth/logout-all", True, None, None, None),
    ("GET", "/api/v1/users/me", True, None, None, None),
    ("PATCH", "/api/v1/users/me", True, None, {"first_name": "X1"}, None),
    ("DELETE", "/api/v1/users/me", True, None, None, None),
    ("PUT", "/api/v1/users/me/bio", True, None, {"about": "Hi"}, None),
    ("PUT", "/api/v1/users/me/avatar", True, None, None, "png"),
    ("POST", "/api/v1/posts", True, None,
     {"name": "Hello", "description": "Long enough desc", "category": "story"},
     None),
    ("PATCH", "/api/v1/posts/{post_id}", True, "/api/v1/posts/{post_id}",
     {"name": "Hijack"}, None),
    ("DELETE", "/api/v1/posts/{post_id}", True, "/api/v1/posts/{post_id}",
     None, None),
    ("POST", "/api/v1/posts/{post_id}/photo", True,
     "/api/v1/posts/{post_id}/photo", None, "png"),
    ("POST", "/api/v1/posts/{post_id}/comments", True, None,
     {"text": "Comment ok"}, None),
    ("PATCH",
     "/api/v1/posts/{post_id}/comments/{comment_id}", True,
     "/api/v1/posts/{post_id}/comments/{comment_id}",
     {"text": "Hijack text"}, None),
    ("DELETE",
     "/api/v1/posts/{post_id}/comments/{comment_id}", True,
     "/api/v1/posts/{post_id}/comments/{comment_id}",
     None, None),
    ("POST", "/api/v1/posts/{post_id}/reactions", True, None,
     {"reaction": "like"}, None),
    ("POST", "/api/v1/tags", True, None, {"name": "music"}, None),
]


def _render_url(tpl: str, post_id: int, comment_id: int) -> str:
    return tpl.replace("{post_id}", str(post_id)).replace(
        "{comment_id}", str(comment_id)
    )


def _request_kwargs(json_body, files_marker):
    kwargs = {}
    if json_body is not None:
        kwargs["json"] = json_body
    if files_marker == "png":
        kwargs["files"] = {"file": ("a.png", png_bytes(), "image/png")}
    return kwargs


@pytest.mark.parametrize(
    ("method", "url_tpl", "requires_auth", "_ownership_tpl", "json_body", "files_marker"),
    PROTECTED_ENDPOINTS,
)
async def test_anonymous_is_rejected(
    client,
    post_factory,
    comment_factory,
    method,
    url_tpl,
    requires_auth,
    _ownership_tpl,
    json_body,
    files_marker,
):
    if not requires_auth:
        pytest.skip("public endpoint")
    post = await post_factory()
    comment = await comment_factory(post_id=post.pk)
    url = _render_url(url_tpl, post.pk, comment.pk)
    resp = await client.request(
        method, url, **_request_kwargs(json_body, files_marker)
    )
    assert resp.status_code in (401, 403), (
        f"{method} {url} returned {resp.status_code}"
    )


@pytest.mark.parametrize(
    ("method", "url_tpl", "_requires_auth", "ownership_tpl", "json_body", "files_marker"),
    [t for t in PROTECTED_ENDPOINTS if t[3] is not None],
)
async def test_non_owner_is_forbidden(
    auth_client,
    post_factory,
    comment_factory,
    user_factory,
    method,
    url_tpl,
    _requires_auth,
    ownership_tpl,
    json_body,
    files_marker,
):
    client, _user = auth_client
    other = await user_factory()
    post = await post_factory(author_id=other.pk)
    comment = await comment_factory(post_id=post.pk, author_id=other.pk)
    url = _render_url(ownership_tpl, post.pk, comment.pk)
    resp = await client.request(
        method, url, **_request_kwargs(json_body, files_marker)
    )
    assert resp.status_code in (403, 404), (
        f"{method} {url} returned {resp.status_code}"
    )
