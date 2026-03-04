import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

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
    database_url = os.environ.get(
        "DATABASE_URL",
        "host=localhost port=5438 dbname=moderation_db user=moderation password=moderation",
    )
    pool = create_connection_pool(database_url)
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
    try:
        with get_connection(request.app.state.connection_pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception as error:
        return {"status": "error", "database": str(error)}
