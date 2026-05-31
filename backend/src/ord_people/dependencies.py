import logging
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Request, status

from ord_people.infra.logging import user_id_var
from ord_people.services.auth import AuthService
from ord_people.services.comment import CommentService
from ord_people.services.post import PostService
from ord_people.services.reaction import ReactionService
from ord_people.services.tag import TagService
from ord_people.services.user import UserService

logger = logging.getLogger(__name__)

SESSION_COOKIE = "session_id"


def get_auth_service(request: Request) -> AuthService:
    return request.app.state.auth_service


def get_user_service(request: Request) -> UserService:
    return request.app.state.user_service


def get_post_service(request: Request) -> PostService:
    return request.app.state.post_service


def get_comment_service(request: Request) -> CommentService:
    return request.app.state.comment_service


def get_reaction_service(request: Request) -> ReactionService:
    return request.app.state.reaction_service


def get_tag_service(request: Request) -> TagService:
    return request.app.state.tag_service


class CurrentUser:
    def __init__(self, user_id: int, username: str, is_admin: bool) -> None:
        self.user_id = user_id
        self.username = username
        self.is_admin = is_admin


async def _resolve_user(
    auth: AuthService, signed_sid: str | None
) -> CurrentUser | None:
    payload = await auth.resolve_session(signed_sid)
    if not payload:
        logger.debug("session_resolve_empty")
        return None
    user_id = payload["user_id"]
    resolved = CurrentUser(
        user_id=int(user_id) if isinstance(user_id, int | str) else 0,
        username=str(payload["username"]),
        is_admin=bool(payload.get("is_admin", False)),
    )
    user_id_var.set(str(resolved.user_id))
    logger.debug(
        "session_resolved user_id=%d username=%s is_admin=%s",
        resolved.user_id,
        resolved.username,
        resolved.is_admin,
    )
    return resolved


async def optional_user(
    auth: Annotated[AuthService, Depends(get_auth_service)],
    session_id: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> CurrentUser | None:
    return await _resolve_user(auth, session_id)


async def current_user(
    user: Annotated[CurrentUser | None, Depends(optional_user)],
) -> CurrentUser:
    if user is None:
        logger.info("auth_required_denied")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    return user


async def admin_user(
    user: Annotated[CurrentUser, Depends(current_user)],
) -> CurrentUser:
    if not user.is_admin:
        logger.warning(
            "admin_required_denied user_id=%d username=%s",
            user.user_id,
            user.username,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin required"
        )
    return user
