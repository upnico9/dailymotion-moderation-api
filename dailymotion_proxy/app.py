import logging

from fastapi import FastAPI

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

app = FastAPI(title="Dailymotion API Proxy")
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
