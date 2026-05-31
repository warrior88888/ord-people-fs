from fastapi import APIRouter

from ord_people.api.auth import router as auth_router
from ord_people.api.comments import router as comments_router
from ord_people.api.posts import router as posts_router
from ord_people.api.reactions import router as reactions_router
from ord_people.api.tags import router as tags_router
from ord_people.api.users import router as users_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(posts_router)
api_router.include_router(comments_router)
api_router.include_router(reactions_router)
api_router.include_router(tags_router)

__all__ = ["api_router"]
