from fastapi import FastAPI

app = FastAPI(title="Moderation Queue API")


@app.get("/health")
def health():
    return {"status": "ok"}
