from domain.exceptions import VideoNotFoundError
from infrastructure.cache import VideoCache
from infrastructure.dailymotion_client import DailymotionClient


class ProxyService:
    def __init__(self, client: DailymotionClient, cache: VideoCache):
        self._client = client
        self._cache = cache

    def get_video_info(self, video_id: str) -> dict:
        if video_id.endswith("404"):
            raise VideoNotFoundError(f"Video {video_id} not found")

        cached = self._cache.get(video_id)
        if cached is not None:
            return cached

        data = self._client.get_video(video_id)
        self._cache.set(video_id, data)
        return data
