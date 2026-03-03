import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from infrastructure.database import create_connection_pool, initialize_database, get_connection


@asynccontextmanager
async def lifespan(application: FastAPI):
    database_url = os.environ.get(
        "DATABASE_URL",
        "host=localhost port=5438 dbname=moderation_db user=moderation password=moderation",
    )
    application.state.connection_pool = create_connection_pool(database_url)
    initialize_database(application.state.connection_pool)
    yield
    application.state.connection_pool.closeall()


app = FastAPI(title="Moderation Queue API", lifespan=lifespan)


@app.get("/health")
def health(request: Request):
    try:
        with get_connection(request.app.state.connection_pool) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception as error:
        return {"status": "error", "database": str(error)}
