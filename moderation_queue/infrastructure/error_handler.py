import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from domain.exceptions import (
    AuthorizationError,
    InvalidRequestError,
    InvalidStatusError,
    VideoAlreadyExistsError,
    VideoNotFoundError,
    VideoNotPendingError,
)

logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(VideoNotFoundError)
    async def video_not_found_handler(request: Request, exc: VideoNotFoundError):
        return JSONResponse(status_code=404, content={"error": str(exc)})

    @app.exception_handler(VideoAlreadyExistsError)
    async def video_already_exists_handler(request: Request, exc: VideoAlreadyExistsError):
        return JSONResponse(status_code=409, content={"error": str(exc)})

    @app.exception_handler(VideoNotPendingError)
    async def video_not_pending_handler(request: Request, exc: VideoNotPendingError):
        return JSONResponse(status_code=400, content={"error": str(exc)})

    @app.exception_handler(InvalidStatusError)
    async def invalid_status_handler(request: Request, exc: InvalidStatusError):
        return JSONResponse(status_code=400, content={"error": str(exc)})

    @app.exception_handler(AuthorizationError)
    async def authorization_handler(request: Request, exc: AuthorizationError):
        return JSONResponse(status_code=401, content={"error": str(exc)})

    @app.exception_handler(InvalidRequestError)
    async def invalid_request_handler(request: Request, exc: InvalidRequestError):
        return JSONResponse(status_code=400, content={"error": str(exc)})

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        logger.error("Unhandled error: %s", exc, exc_info=True)
        return JSONResponse(status_code=500, content={"error": "Internal server error"})
