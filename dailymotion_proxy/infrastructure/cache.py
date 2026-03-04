import time
from typing import Callable


class VideoCache:

    def __init__(self, default_ttl: int = 300, time_func: Callable[[], float] = time.time):
        self._default_ttl = default_ttl
        self._time_func = time_func
        self._cache: dict = {}

    def get(self, video_id: str) -> dict | None:
        entry = self._cache.get(video_id)
        if entry is None:
            return None

        if self._time_func() > entry["expires_at"]:
            del self._cache[video_id]
            return None

        return entry["data"]

    def set(self, video_id: str, data: dict, ttl: int | None = None) -> None:
        effective_ttl = ttl if ttl is not None else self._default_ttl
        self._cache[video_id] = {
            "data": data,
            "expires_at": self._time_func() + effective_ttl,
        }

    def invalidate(self, video_id: str) -> None:
        self._cache.pop(video_id, None)

    def clear(self) -> None:
        self._cache.clear()
