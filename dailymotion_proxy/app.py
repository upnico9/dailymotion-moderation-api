from fastapi import FastAPI

app = FastAPI(title="Dailymotion API Proxy")


@app.get("/health")
def health():
    return {"status": "ok"}
