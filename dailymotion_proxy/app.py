from fastapi import FastAPI

from infrastructure.error_handler import register_error_handlers

app = FastAPI(title="Dailymotion API Proxy")
register_error_handlers(app)


@app.get("/health")
def health():
    return {"status": "ok"}
