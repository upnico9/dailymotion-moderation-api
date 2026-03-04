import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

import config
from infrastructure.cache import VideoCache
from infrastructure.dailymotion_client import DailymotionClient
from infrastructure.error_handler import register_error_handlers
from routes.proxy_routes import router
from services.proxy_service import ProxyService

app = FastAPI(
    title="Dailymotion API Proxy",
    description="Proxy service for the Dailymotion public API. "
    "Fetches video metadata and caches results in memory with a configurable TTL.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["Content-Type"],
)
register_error_handlers(app)

cache = VideoCache(default_ttl=config.CACHE_TTL, max_size=config.CACHE_MAX_SIZE)
client = DailymotionClient(
    base_url=config.DAILYMOTION_API_URL,
    timeout=config.DAILYMOTION_API_TIMEOUT,
)
app.state.proxy_service = ProxyService(client=client, cache=cache)

app.include_router(router)

@app.get("/health")
def health():
    return {"status": "ok"}
