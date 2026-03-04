import logging
from typing import Callable

import requests

from domain.exceptions import DailymotionApiError, VideoNotFoundError

logger = logging.getLogger(__name__)


class DailymotionClient:

    def __init__(
        self,
        base_url: str,
        timeout: int,
        http_get: Callable = requests.get,
    ):
        self._base_url = base_url
        self._timeout = timeout
        self._http_get = http_get

    def get_video(self, video_id: str) -> dict:
        url = f"{self._base_url}/video/{video_id}"

        try:
            response = self._http_get(url, timeout=self._timeout)
        except requests.exceptions.Timeout:
            logger.error("API timeout for video %s", video_id)
            raise DailymotionApiError("API timeout")
        except requests.exceptions.RequestException as e:
            logger.error("Request error for video %s: %s", video_id, e)
            raise DailymotionApiError(f"Request error: {e}")

        if response.status_code == 404:
            raise VideoNotFoundError(f"Video {video_id} not found")

        if response.status_code != 200:
            logger.error("API error for video %s: HTTP %s", video_id, response.status_code)
            raise DailymotionApiError(f"API error: {response.status_code}")

        try:
            return response.json()
        except ValueError:
            logger.error("Invalid JSON response for video %s", video_id)
            raise DailymotionApiError("Invalid API response")
