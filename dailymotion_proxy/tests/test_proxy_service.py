from unittest.mock import MagicMock

import pytest

from domain.exceptions import DailymotionApiError, VideoNotFoundError
from infrastructure.cache import VideoCache
from services.proxy_service import ProxyService


class TestProxyService:

    def setup_method(self):
        self.mock_client = MagicMock()
        self.cache = VideoCache(default_ttl=300)
        self.service = ProxyService(client=self.mock_client, cache=self.cache)
        self.sample_data = {
            "title": "Dailymotion Spirit Movie",
            "channel": "creation",
            "owner": "Dailymotion",
        }

    def test_video_ending_404(self):
        with pytest.raises(VideoNotFoundError):
            self.service.get_video_info("10404")

        self.mock_client.get_video.assert_not_called()

    def test_video_ending_404_variants(self):
        for video_id in ["404", "1404", "10404", "abc404"]:
            with pytest.raises(VideoNotFoundError):
                self.service.get_video_info(video_id)

    def test_cache_hit(self):
        self.cache.set("x2m8jpp", self.sample_data)

        result = self.service.get_video_info("x2m8jpp")

        assert result == self.sample_data
        self.mock_client.get_video.assert_not_called()

    def test_cache_miss_calls_api(self):
        self.mock_client.get_video.return_value = self.sample_data

        result = self.service.get_video_info("x2m8jpp")

        assert result == self.sample_data
        self.mock_client.get_video.assert_called_once_with("x2m8jpp")
        assert self.cache.get("x2m8jpp") == self.sample_data

    def test_cache_miss_then_hit(self):
        self.mock_client.get_video.return_value = self.sample_data

        result1 = self.service.get_video_info("x2m8jpp")
        result2 = self.service.get_video_info("x2m8jpp")

        assert result1 == result2 == self.sample_data
        self.mock_client.get_video.assert_called_once()

    def test_api_error_propagates(self):
        self.mock_client.get_video.side_effect = DailymotionApiError("API timeout")

        with pytest.raises(DailymotionApiError, match="API timeout"):
            self.service.get_video_info("x2m8jpp")

    def test_api_not_found_propagates(self):
        self.mock_client.get_video.side_effect = VideoNotFoundError("Not found")

        with pytest.raises(VideoNotFoundError):
            self.service.get_video_info("x2m8jpp")

    def test_api_error_does_not_cache(self):
        self.mock_client.get_video.side_effect = DailymotionApiError("API error")

        with pytest.raises(DailymotionApiError):
            self.service.get_video_info("x2m8jpp")

        assert self.cache.get("x2m8jpp") is None
