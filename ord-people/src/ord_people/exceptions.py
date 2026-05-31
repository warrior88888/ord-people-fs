from pydantic import BaseModel, ConfigDict


class ErrorResponse(BaseModel):
    """Uniform error envelope returned by all non-2xx responses."""

    model_config = ConfigDict(json_schema_extra={"example": {"detail": "Not found"}})

    detail: str


class AppError(Exception):
    status_code: int = 500
    detail: str = "Internal error"


class NotFoundError(AppError):
    status_code = 404
    detail = "Not found"


class ConflictError(AppError):
    status_code = 409
    detail = "Conflict"


class ValidationError(AppError):
    status_code = 400
    detail = "Bad request"


class UnauthorizedError(AppError):
    status_code = 401
    detail = "Unauthorized"


class ForbiddenError(AppError):
    status_code = 403
    detail = "Forbidden"


class UserNotFoundError(NotFoundError):
    detail = "User not found"


class UsernameAlreadyTakenError(ConflictError):
    detail = "Username already taken"


class InvalidCredentialsError(UnauthorizedError):
    detail = "Invalid credentials"


class PostNotFoundError(NotFoundError):
    detail = "Post not found"


class CommentNotFoundError(NotFoundError):
    detail = "Comment not found"


class TagNotFoundError(NotFoundError):
    detail = "Tag not found"


class TagAlreadyExistsError(ConflictError):
    detail = "Tag already exists"


class AvatarTooLargeError(ValidationError):
    detail = "Avatar too large"


class InvalidImageError(ValidationError):
    detail = "Invalid image file"


class UnsupportedImageTypeError(ValidationError):
    status_code = 415
    detail = "Unsupported image type"
