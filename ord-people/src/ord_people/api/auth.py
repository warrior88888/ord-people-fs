import logging
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response, status

from ord_people.config.constatns import rate as rl
from ord_people.config.settings import get_settings
from ord_people.dependencies import (
    SESSION_COOKIE,
    CurrentUser,
    current_user,
    get_auth_service,
)
from ord_people.exceptions import ErrorResponse
from ord_people.infra.rate_limit import rate_limit
from ord_people.schemas.auth import LoginSchema, RegisterResponseSchema, RegisterSchema
from ord_people.services.auth import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

_RATE_LIMITED: dict[int | str, dict[str, object]] = {
    429: {
        "model": ErrorResponse,
        "description": "Rate limit exceeded. "
        "`Retry-After` header indicates the window in seconds.",
    },
}


def _set_cookie(response: Response, value: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=SESSION_COOKIE,
        value=value,
        max_age=settings.auth.session_ttl,
        httponly=True,
        secure=settings.app.cookie_secure,
        samesite="lax",
    )
    logger.debug("session_cookie_set max_age=%d", settings.auth.session_ttl)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=RegisterResponseSchema,
    dependencies=[Depends(rate_limit("auth.register", *rl.AUTH_REGISTER))],
    summary="Register a new user and start a session",
    description=(
        "Creates a user, signs in immediately and sets the `session_id` "
        "HTTP-only cookie. No separate login call is required after success."
    ),
    responses={
        409: {"model": ErrorResponse, "description": "Username already taken."},
        **_RATE_LIMITED,
    },
)
async def register(
    data: RegisterSchema,
    response: Response,
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> RegisterResponseSchema:
    logger.info("api_register username=%s", data.username)
    user_id, username = await auth.register(data)
    signed = await auth.login(
        LoginSchema(username=data.username, password=data.password)
    )
    _set_cookie(response, signed)
    return RegisterResponseSchema(user_id=user_id, username=username)


@router.post(
    "/login",
    dependencies=[Depends(rate_limit("auth.login", *rl.AUTH_LOGIN))],
    summary="Authenticate and set the session cookie",
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Invalid credentials or account deactivated.",
        },
        **_RATE_LIMITED,
    },
)
async def login(
    data: LoginSchema,
    response: Response,
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> dict[str, str]:
    logger.info("api_login username=%s", data.username)
    signed = await auth.login(data)
    _set_cookie(response, signed)
    return {"status": "ok"}


@router.post(
    "/logout",
    dependencies=[Depends(rate_limit("auth.logout", *rl.AUTH_LOGOUT))],
    summary="Terminate the current session",
    description=(
        "Idempotent: clears the `session_id` cookie and revokes the current "
        "session if present. Always returns 200, including when no session is sent."
    ),
    responses=_RATE_LIMITED,
)
async def logout(
    response: Response,
    auth: Annotated[AuthService, Depends(get_auth_service)],
    session_id: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> dict[str, str]:
    logger.info("api_logout has_session=%s", session_id is not None)
    if session_id:
        await auth.logout(session_id)
    response.delete_cookie(SESSION_COOKIE)
    return {"status": "ok"}


@router.post(
    "/logout-all",
    dependencies=[Depends(rate_limit("auth.logout_all", *rl.AUTH_LOGOUT_ALL))],
    summary="Revoke every active session for the current user",
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated."},
        **_RATE_LIMITED,
    },
)
async def logout_all(
    response: Response,
    user: Annotated[CurrentUser, Depends(current_user)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> dict[str, str]:
    logger.info("api_logout_all user_id=%d", user.user_id)
    await auth.logout_all(user.user_id)
    response.delete_cookie(SESSION_COOKIE)
    return {"status": "ok"}
