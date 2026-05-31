import datetime
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from ord_people.config.constatns import rate as rl
from ord_people.dependencies import (
    CurrentUser,
    current_user,
    get_post_service,
    optional_user,
)
from ord_people.exceptions import ErrorResponse
from ord_people.infra.rate_limit import rate_limit
from ord_people.schemas.pagination import PaginatedResult, PaginationParams
from ord_people.schemas.post import (
    PhotoUploadResponse,
    PostCreateSchema,
    PostFeedFilters,
    PostLightSchema,
    PostSchema,
    PostUpdateSchema,
)
from ord_people.services.post import PostService
from ord_people.utils.enums import PostCategory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/posts", tags=["posts"])

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
_OWNERSHIP: dict[int | str, dict[str, object]] = {
    403: {
        "model": ErrorResponse,
        "description": "Caller is neither the post author nor an admin.",
    },
    404: {"model": ErrorResponse, "description": "Post not found."},
}


@router.get(
    "",
    response_model=PaginatedResult[PostLightSchema],
    summary="Paginated post feed with optional filters",
    description=(
        "Anonymous-friendly. The unfiltered feed (no category, tags or "
        "date range) is cached; any filter combination bypasses the cache."
    ),
)
async def list_feed(
    svc: Annotated[PostService, Depends(get_post_service)],
    pagination: Annotated[PaginationParams, Depends()],
    category: PostCategory | None = None,
    tag_ids: Annotated[list[int] | None, Query()] = None,
    date_from: datetime.datetime | None = None,
    date_to: datetime.datetime | None = None,
) -> PaginatedResult[PostLightSchema]:
    logger.debug(
        "api_posts_feed limit=%d offset=%d category=%s tags=%d",
        pagination.limit,
        pagination.offset,
        category,
        len(tag_ids or []),
    )
    filters = PostFeedFilters(
        category=category,
        tag_ids=tag_ids or [],
        date_from=date_from,
        date_to=date_to,
    )
    return await svc.list_feed(
        limit=pagination.limit, offset=pagination.offset, filters=filters
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=PostSchema,
    dependencies=[Depends(rate_limit("post.create", *rl.POST_CREATE))],
    summary="Create a post authored by the current user",
    responses={**_AUTH_REQUIRED, **_RATE_LIMITED},
)
async def create_post(
    data: PostCreateSchema,
    user: Annotated[CurrentUser, Depends(current_user)],
    svc: Annotated[PostService, Depends(get_post_service)],
) -> PostSchema:
    logger.info("api_create_post user_id=%d name=%s", user.user_id, data.name)
    return await svc.create(user.user_id, data)


@router.get(
    "/{post_id}",
    response_model=PostSchema,
    summary="Fetch a single post",
    description=(
        "Anonymous-friendly. The `my_reaction` field is populated only when "
        "the caller is authenticated; it is `null` otherwise."
    ),
    responses={404: {"model": ErrorResponse, "description": "Post not found."}},
)
async def get_post(
    post_id: int,
    svc: Annotated[PostService, Depends(get_post_service)],
    user: Annotated[CurrentUser | None, Depends(optional_user)],
) -> PostSchema:
    logger.debug(
        "api_get_post post_id=%d user_id=%s",
        post_id,
        user.user_id if user else None,
    )
    return await svc.get(post_id, current_user_id=user.user_id if user else None)


@router.patch(
    "/{post_id}",
    response_model=PostSchema,
    dependencies=[Depends(rate_limit("post.update", *rl.POST_UPDATE))],
    summary="Partially update a post (author only)",
    description="Admins cannot edit foreign posts, only delete them.",
    responses={
        401: _AUTH_REQUIRED[401],
        **_OWNERSHIP,
        **_RATE_LIMITED,
    },
)
async def update_post(
    post_id: int,
    data: PostUpdateSchema,
    user: Annotated[CurrentUser, Depends(current_user)],
    svc: Annotated[PostService, Depends(get_post_service)],
) -> PostSchema:
    logger.info("api_update_post post_id=%d user_id=%d", post_id, user.user_id)
    return await svc.update(post_id, user.user_id, data)


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(rate_limit("post.delete", *rl.POST_DELETE))],
    summary="Delete a post (author or admin)",
    description="Removes the post row and its photo from storage. Hard delete.",
    responses={
        401: _AUTH_REQUIRED[401],
        **_OWNERSHIP,
        **_RATE_LIMITED,
    },
)
async def delete_post(
    post_id: int,
    user: Annotated[CurrentUser, Depends(current_user)],
    svc: Annotated[PostService, Depends(get_post_service)],
) -> None:
    logger.info(
        "api_delete_post post_id=%d user_id=%d is_admin=%s",
        post_id,
        user.user_id,
        user.is_admin,
    )
    await svc.delete(post_id, user.user_id, user.is_admin)


@router.post(
    "/{post_id}/photo",
    response_model=PhotoUploadResponse,
    dependencies=[Depends(rate_limit("post.photo", *rl.POST_PHOTO_UPLOAD))],
    summary="Upload (replace) the post's photo (author only)",
    description=(
        "Multipart upload. Re-encoded server-side to WebP; the previous "
        "photo, if any, is deleted from storage."
    ),
    responses={
        401: _AUTH_REQUIRED[401],
        403: {"model": ErrorResponse, "description": "Caller is not the post author."},
        404: {"model": ErrorResponse, "description": "Post not found."},
        **_RATE_LIMITED,
    },
)
async def upload_photo(
    post_id: int,
    file: Annotated[UploadFile, File()],
    user: Annotated[CurrentUser, Depends(current_user)],
    svc: Annotated[PostService, Depends(get_post_service)],
) -> dict[str, str]:
    logger.info(
        "api_upload_post_photo post_id=%d user_id=%d filename=%s",
        post_id,
        user.user_id,
        file.filename,
    )
    raw = await file.read()
    url = await svc.upload_photo(post_id, user.user_id, raw)
    return {"photo_url": url}


@router.delete(
    "/{post_id}/photo",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(rate_limit("post.photo.delete", *rl.POST_PHOTO_DELETE))],
    summary="Remove a post's photo (author only)",
    description=(
        "Clears `photo_key` and deletes the stored object. Idempotent: "
        "returns 204 even when no photo was attached."
    ),
    responses={
        401: _AUTH_REQUIRED[401],
        403: {"model": ErrorResponse, "description": "Caller is not the post author."},
        404: {"model": ErrorResponse, "description": "Post not found."},
        **_RATE_LIMITED,
    },
)
async def delete_photo(
    post_id: int,
    user: Annotated[CurrentUser, Depends(current_user)],
    svc: Annotated[PostService, Depends(get_post_service)],
) -> None:
    logger.info(
        "api_delete_post_photo post_id=%d user_id=%d", post_id, user.user_id
    )
    await svc.delete_photo(post_id, user.user_id)
