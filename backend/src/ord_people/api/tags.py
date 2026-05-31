import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status

from ord_people.config.constatns import rate as rl
from ord_people.dependencies import CurrentUser, admin_user, get_tag_service
from ord_people.exceptions import ErrorResponse
from ord_people.infra.rate_limit import rate_limit
from ord_people.schemas.tag import TagCreateSchema, TagSchema
from ord_people.services.tag import TagService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tags", tags=["tags"])


@router.get(
    "",
    response_model=list[TagSchema],
    summary="List every tag in the catalog",
)
async def list_tags(
    svc: Annotated[TagService, Depends(get_tag_service)],
) -> list[TagSchema]:
    logger.debug("api_list_tags")
    return await svc.list_all()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=TagSchema,
    dependencies=[Depends(rate_limit("tag.create", *rl.TAG_CREATE))],
    summary="Create a tag (admin only)",
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated."},
        403: {"model": ErrorResponse, "description": "Admin privileges required."},
        409: {
            "model": ErrorResponse,
            "description": "Tag with this name already exists.",
        },
        429: {
            "model": ErrorResponse,
            "description": "Rate limit exceeded."
            " `Retry-After` header indicates the window in seconds.",
        },
    },
)
async def create_tag(
    data: TagCreateSchema,
    admin: Annotated[CurrentUser, Depends(admin_user)],
    svc: Annotated[TagService, Depends(get_tag_service)],
) -> TagSchema:
    logger.info("api_create_tag name=%s admin_id=%d", data.name, admin.user_id)
    return await svc.create(data)
