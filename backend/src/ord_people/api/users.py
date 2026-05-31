import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, Response, UploadFile, status

from ord_people.config.constatns import rate as rl
from ord_people.config.constatns.media import ALLOWED_IMAGE_CONTENT_TYPES
from ord_people.dependencies import (
    SESSION_COOKIE,
    CurrentUser,
    current_user,
    get_post_service,
    get_user_service,
)
from ord_people.exceptions import ErrorResponse, UnsupportedImageTypeError
from ord_people.infra.rate_limit import rate_limit
from ord_people.schemas.bio import BioSchema, BioUpdateSchema
from ord_people.schemas.pagination import PaginatedResult, PaginationParams
from ord_people.schemas.post import PostFeedFilters, PostLightSchema
from ord_people.schemas.user import (
    AvatarUploadResponse,
    UserLightSchema,
    UserSchema,
    UserUpdateSchema,
)
from ord_people.services.post import PostService
from ord_people.services.user import UserService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["users"])

_RATE_LIMITED: dict[int | str, dict[str, object]] = {
    429: {
        "model": ErrorResponse,
        "description": "Rate limit exceeded."
        " `Retry-After` header indicates the window in seconds.",
    },
}
_AUTH_REQUIRED: dict[int | str, dict[str, object]] = {
    401: {"model": ErrorResponse, "description": "Not authenticated."},
}
_USER_NOT_FOUND: dict[int | str, dict[str, object]] = {
    404: {"model": ErrorResponse, "description": "User not found."},
}


@router.get(
    "",
    response_model=PaginatedResult[UserLightSchema],
    summary="Paginated public user directory",
    description="Anonymous users are excluded. Results are cached.",
)
async def get_users_feed(
    svc: Annotated[UserService, Depends(get_user_service)],
    pagination: Annotated[PaginationParams, Depends()],
) -> PaginatedResult[UserLightSchema]:
    logger.debug(
        "api_users_feed limit=%d offset=%d", pagination.limit, pagination.offset
    )
    return await svc.list_feed(limit=pagination.limit, offset=pagination.offset)


@router.get(
    "/me",
    response_model=UserSchema,
    summary="Profile of the authenticated user",
    responses=_AUTH_REQUIRED,
)
async def get_me(
    user: Annotated[CurrentUser, Depends(current_user)],
    svc: Annotated[UserService, Depends(get_user_service)],
) -> UserSchema:
    logger.debug("api_get_me user_id=%d", user.user_id)
    return await svc.get_by_username(user.username)


@router.patch(
    "/me",
    response_model=UserSchema,
    dependencies=[Depends(rate_limit("user.update", *rl.USER_UPDATE))],
    summary="Partially update the authenticated user's profile",
    responses={**_AUTH_REQUIRED, **_RATE_LIMITED},
)
async def update_me(
    data: UserUpdateSchema,
    user: Annotated[CurrentUser, Depends(current_user)],
    svc: Annotated[UserService, Depends(get_user_service)],
) -> UserSchema:
    logger.info("api_update_me user_id=%d", user.user_id)
    return await svc.update_me(user.user_id, data)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(rate_limit("user.delete", *rl.USER_DELETE))],
    summary="Anonymize the authenticated account",
    description=(
        "Performs a soft-delete: the row is preserved but the username is "
        "replaced with `deleted-<id>`, personal fields are wiped, the avatar "
        "is removed, the bio is dropped and all sessions are revoked. "
        "The operation is irreversible."
    ),
    responses={**_AUTH_REQUIRED, **_RATE_LIMITED},
)
async def delete_me(
    response: Response,
    user: Annotated[CurrentUser, Depends(current_user)],
    svc: Annotated[UserService, Depends(get_user_service)],
) -> None:
    logger.info("api_delete_me user_id=%d", user.user_id)
    await svc.delete_me(user.user_id)
    response.delete_cookie(SESSION_COOKIE)


@router.put(
    "/me/avatar",
    response_model=AvatarUploadResponse,
    dependencies=[Depends(rate_limit("user.avatar", *rl.AVATAR_UPLOAD))],
    summary="Upload (replace) the authenticated user's avatar",
    description=(
        "Multipart upload. The image is re-encoded server-side to WebP and "
        "the previous avatar (if any) is deleted. Allowed input types are "
        "the values in `ALLOWED_IMAGE_CONTENT_TYPES`."
    ),
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Image exceeds size limit or is unreadable.",
        },
        415: {"model": ErrorResponse, "description": "Unsupported image content type."},
        **_AUTH_REQUIRED,
        **_RATE_LIMITED,
    },
)
async def upload_avatar(
    file: Annotated[UploadFile, File()],
    user: Annotated[CurrentUser, Depends(current_user)],
    svc: Annotated[UserService, Depends(get_user_service)],
) -> dict[str, str]:
    logger.info(
        "api_upload_avatar user_id=%d filename=%s content_type=%s",
        user.user_id,
        file.filename,
        file.content_type,
    )
    if file.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise UnsupportedImageTypeError
    raw = await file.read()
    url = await svc.upload_avatar(user.user_id, raw)
    return {"avatar_url": url}


@router.delete(
    "/me/avatar",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(rate_limit("user.avatar.delete", *rl.AVATAR_DELETE))],
    summary="Remove the authenticated user's avatar",
    description=(
        "Clears `avatar_key` and deletes the stored object. Idempotent: "
        "returns 204 even when no avatar was set."
    ),
    responses={**_AUTH_REQUIRED, **_RATE_LIMITED},
)
async def delete_avatar(
    user: Annotated[CurrentUser, Depends(current_user)],
    svc: Annotated[UserService, Depends(get_user_service)],
) -> None:
    logger.info("api_delete_avatar user_id=%d", user.user_id)
    await svc.delete_avatar(user.user_id)


@router.put(
    "/me/bio",
    response_model=BioSchema,
    dependencies=[Depends(rate_limit("user.bio", *rl.BIO_UPDATE))],
    summary="Upsert the authenticated user's bio",
    description=(
        "Creates the bio row if missing, otherwise patches the provided "
        "fields. Empty strings for phone/vk/max links clear the value."
    ),
    responses={**_AUTH_REQUIRED, **_RATE_LIMITED},
)
async def update_bio(
    data: BioUpdateSchema,
    user: Annotated[CurrentUser, Depends(current_user)],
    svc: Annotated[UserService, Depends(get_user_service)],
) -> BioSchema:
    logger.info("api_update_bio user_id=%d", user.user_id)
    return await svc.update_bio(user.user_id, data)


@router.get(
    "/{username}",
    response_model=UserSchema,
    summary="Public profile by username",
    responses=_USER_NOT_FOUND,
)
async def get_user(
    username: str,
    svc: Annotated[UserService, Depends(get_user_service)],
) -> UserSchema:
    logger.debug("api_get_user username=%s", username)
    return await svc.get_by_username(username)


@router.get(
    "/{username}/posts",
    response_model=PaginatedResult[PostLightSchema],
    summary="Paginated posts authored by a given user",
    responses=_USER_NOT_FOUND,
)
async def get_user_posts(
    username: str,
    user_svc: Annotated[UserService, Depends(get_user_service)],
    post_svc: Annotated[PostService, Depends(get_post_service)],
    pagination: Annotated[PaginationParams, Depends()],
) -> PaginatedResult[PostLightSchema]:
    logger.debug(
        "api_get_user_posts username=%s limit=%d offset=%d",
        username,
        pagination.limit,
        pagination.offset,
    )
    profile = await user_svc.get_by_username(username)
    return await post_svc.list_feed(
        limit=pagination.limit,
        offset=pagination.offset,
        filters=PostFeedFilters(),
        author_id=profile.pk,
    )
