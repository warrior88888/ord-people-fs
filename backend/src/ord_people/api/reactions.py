import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from ord_people.config.constatns import rate as rl
from ord_people.dependencies import (
    CurrentUser,
    current_user,
    get_reaction_service,
)
from ord_people.exceptions import ErrorResponse
from ord_people.infra.rate_limit import rate_limit
from ord_people.schemas.reaction import (
    ReactionToggleResponse,
    ReactionToggleSchema,
)
from ord_people.services.reaction import ReactionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/posts", tags=["reactions"])


@router.post(
    "/{post_id}/reactions",
    response_model=ReactionToggleResponse,
    dependencies=[Depends(rate_limit("reaction.toggle", *rl.REACTION_TOGGLE))],
    summary="Toggle the caller's reaction on a post",
    description=(
        "Single endpoint with toggle semantics:\n\n"
        "- no existing reaction → the reaction is added;\n"
        "- existing reaction of the same type → "
        "it is removed (`my_reaction` becomes `null`);\n"
        "- existing reaction of a different type → it is replaced.\n\n"
        "The response always carries the up-to-date counts and the caller's "
        "current reaction after the operation."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated."},
        404: {"model": ErrorResponse, "description": "Post not found."},
        429: {
            "model": ErrorResponse,
            "description": "Rate limit exceeded."
            " `Retry-After` header indicates the window in seconds.",
        },
    },
)
async def toggle_reaction(
    post_id: int,
    data: ReactionToggleSchema,
    user: Annotated[CurrentUser, Depends(current_user)],
    svc: Annotated[ReactionService, Depends(get_reaction_service)],
) -> ReactionToggleResponse:
    logger.info(
        "api_toggle_reaction post_id=%d user_id=%d reaction=%s",
        post_id,
        user.user_id,
        data.reaction,
    )
    counts, my = await svc.toggle(post_id, user.user_id, data.reaction)
    return ReactionToggleResponse(counts=counts, my_reaction=my)
