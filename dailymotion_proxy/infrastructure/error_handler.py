import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from domain.exceptions import DailymotionApiError, VideoNotFoundError

logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(VideoNotFoundError)
    async def video_not_found_handler(request: Request, exc: VideoNotFoundError):
        return JSONResponse(status_code=404, content={"error": str(exc)})

    @app.exception_handler(DailymotionApiError)
    async def dailymotion_api_error_handler(request: Request, exc: DailymotionApiError):
        return JSONResponse(status_code=502, content={"error": str(exc)})

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        logger.error("Unhandled error: %s", exc, exc_info=True)
        return JSONResponse(status_code=500, content={"error": "Internal server error"})
