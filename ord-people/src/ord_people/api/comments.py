import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status

from ord_people.config.constatns import rate as rl
from ord_people.dependencies import (
    CurrentUser,
    current_user,
    get_comment_service,
)
from ord_people.exceptions import ErrorResponse
from ord_people.infra.rate_limit import rate_limit
from ord_people.schemas.comment import (
    CommentCreateSchema,
    CommentSchema,
    CommentUpdateSchema,
)
from ord_people.schemas.pagination import PaginatedResult, PaginationParams
from ord_people.services.comment import CommentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/posts", tags=["comments"])

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
_POST_NOT_FOUND: dict[int | str, dict[str, object]] = {
    404: {"model": ErrorResponse, "description": "Post not found."},
}
_COMMENT_OWNERSHIP: dict[int | str, dict[str, object]] = {
    403: {
        "model": ErrorResponse,
        "description": "Caller is neither the comment author nor an admin.",
    },
    404: {
        "model": ErrorResponse,
        "description": "Post or comment not found, "
        "or comment does not belong to the post.",
    },
}


@router.get(
    "/{post_id}/comments",
    response_model=PaginatedResult[CommentSchema],
    summary="Paginated comments for a post",
    responses=_POST_NOT_FOUND,
)
async def list_comments(
    post_id: int,
    svc: Annotated[CommentService, Depends(get_comment_service)],
    pagination: Annotated[PaginationParams, Depends()],
) -> PaginatedResult[CommentSchema]:
    logger.debug(
        "api_list_comments post_id=%d limit=%d offset=%d",
        post_id,
        pagination.limit,
        pagination.offset,
    )
    return await svc.list_by_post(
        post_id, limit=pagination.limit, offset=pagination.offset
    )


@router.post(
    "/{post_id}/comments",
    status_code=status.HTTP_201_CREATED,
    response_model=CommentSchema,
    dependencies=[Depends(rate_limit("comment.create", *rl.COMMENT_CREATE))],
    summary="Create a comment on a post",
    responses={**_AUTH_REQUIRED, **_POST_NOT_FOUND, **_RATE_LIMITED},
)
async def create_comment(
    post_id: int,
    data: CommentCreateSchema,
    user: Annotated[CurrentUser, Depends(current_user)],
    svc: Annotated[CommentService, Depends(get_comment_service)],
) -> CommentSchema:
    logger.info("api_create_comment post_id=%d user_id=%d", post_id, user.user_id)
    return await svc.create(post_id, user.user_id, data)


@router.patch(
    "/{post_id}/comments/{comment_id}",
    response_model=CommentSchema,
    dependencies=[Depends(rate_limit("comment.update", *rl.COMMENT_UPDATE))],
    summary="Edit a comment (author only)",
    description="Admins cannot edit foreign comments, only delete them.",
    responses={
        **_AUTH_REQUIRED,
        403: {
            "model": ErrorResponse,
            "description": "Caller is not the comment author.",
        },
        404: _COMMENT_OWNERSHIP[404],
        **_RATE_LIMITED,
    },
)
async def update_comment(
    post_id: int,
    comment_id: int,
    data: CommentUpdateSchema,
    user: Annotated[CurrentUser, Depends(current_user)],
    svc: Annotated[CommentService, Depends(get_comment_service)],
) -> CommentSchema:
    logger.info(
        "api_update_comment comment_id=%d post_id=%d user_id=%d",
        comment_id,
        post_id,
        user.user_id,
    )
    return await svc.update(post_id, comment_id, user.user_id, data)


@router.delete(
    "/{post_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(rate_limit("comment.delete", *rl.COMMENT_DELETE))],
    summary="Delete a comment (author or admin)",
    responses={**_AUTH_REQUIRED, **_COMMENT_OWNERSHIP, **_RATE_LIMITED},
)
async def delete_comment(
    post_id: int,
    comment_id: int,
    user: Annotated[CurrentUser, Depends(current_user)],
    svc: Annotated[CommentService, Depends(get_comment_service)],
) -> None:
    logger.info(
        "api_delete_comment comment_id=%d post_id=%d user_id=%d is_admin=%s",
        comment_id,
        post_id,
        user.user_id,
        user.is_admin,
    )
    await svc.delete(post_id, comment_id, user.user_id, user.is_admin)
