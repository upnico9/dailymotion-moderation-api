from fastapi import FastAPI

from infrastructure.cache import VideoCache
from infrastructure.dailymotion_client import DailymotionClient
from infrastructure.error_handler import register_error_handlers
from routes.proxy_routes import router
from services.proxy_service import ProxyService

app = FastAPI(title="Dailymotion API Proxy")
register_error_handlers(app)

cache = VideoCache(default_ttl=300)
client = DailymotionClient()
app.state.proxy_service = ProxyService(client=client, cache=cache)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}
