import os

DAILYMOTION_API_URL = os.environ.get(
    "DAILYMOTION_API_URL", "https://api.dailymotion.com"
)
DAILYMOTION_API_TIMEOUT = int(os.environ.get("DAILYMOTION_API_TIMEOUT", "5"))
CACHE_TTL = int(os.environ.get("CACHE_TTL", "300"))
CACHE_MAX_SIZE = int(os.environ.get("CACHE_MAX_SIZE", "1000"))
