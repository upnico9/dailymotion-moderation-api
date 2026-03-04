import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

import config
from infrastructure.database import create_connection_pool, initialize_database, get_connection
from infrastructure.error_handler import register_error_handlers
from infrastructure.event_dispatcher import EventDispatcher
from repositories.video_repository import VideoRepository
from repositories.video_log_repository import VideoLogRepository
from services.video_log_service import VideoLogService
from services.moderation_service import ModerationService
from routes.moderation_routes import router as moderation_router


@asynccontextmanager
async def lifespan(application: FastAPI):
    pool = create_connection_pool(
        config.DATABASE_URL,
        min_connections=config.DB_POOL_MIN,
        max_connections=config.DB_POOL_MAX,
    )
    initialize_database(pool)
    application.state.connection_pool = pool

    video_repo = VideoRepository(pool)
    video_log_repo = VideoLogRepository(pool)
    event_dispatcher = EventDispatcher()
    video_log_service = VideoLogService(video_log_repo)
    moderation_service = ModerationService(video_repo, video_log_service, event_dispatcher)

    application.state.moderation_service = moderation_service
    application.state.video_log_service = video_log_service

    yield
    pool.closeall()


app = FastAPI(title="Moderation Queue API", lifespan=lifespan)
register_error_handlers(app)
app.include_router(moderation_router)


@app.get("/health")
def health(request: Request):
    return {"status": "ok"}
