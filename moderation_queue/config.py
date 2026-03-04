import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "host=localhost port=5438 dbname=moderation_db user=moderation password=moderation",
)
DB_POOL_MIN = int(os.environ.get("DB_POOL_MIN", "2"))
DB_POOL_MAX = int(os.environ.get("DB_POOL_MAX", "10"))

CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")
