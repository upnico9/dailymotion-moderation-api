from unittest.mock import MagicMock

import pytest
import requests

from domain.exceptions import DailymotionApiError, VideoNotFoundError
from infrastructure.dailymotion_client import DailymotionClient


class TestDailymotionClient:

    def setup_method(self):
        self.mock_get = MagicMock()
        self.client = DailymotionClient(
            base_url="https://api.dailymotion.com",
            timeout=5,
            http_get=self.mock_get,
        )
        self.sample_response = {
            "title": "Test Video",
            "channel": "news",
            "owner": "user123",
        }

    def test_get_video_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_response
        self.mock_get.return_value = mock_response

        result = self.client.get_video("abc123")

        assert result == self.sample_response
        self.mock_get.assert_called_once_with(
            "https://api.dailymotion.com/video/abc123",
            timeout=5,
        )

    def test_get_video_not_found(self):
        mock_response = MagicMock()
        mock_response.status_code = 404
        self.mock_get.return_value = mock_response

        with pytest.raises(VideoNotFoundError, match="abc123"):
            self.client.get_video("abc123")

    def test_get_video_timeout(self):
        self.mock_get.side_effect = requests.exceptions.Timeout()

        with pytest.raises(DailymotionApiError, match="API timeout"):
            self.client.get_video("abc123")

    def test_get_video_connection_error(self):
        self.mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

        with pytest.raises(DailymotionApiError, match="Request error"):
            self.client.get_video("abc123")

    def test_get_video_server_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 500
        self.mock_get.return_value = mock_response

        with pytest.raises(DailymotionApiError, match="API error: 500"):
            self.client.get_video("abc123")

    def test_get_video_invalid_json(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        self.mock_get.return_value = mock_response

        with pytest.raises(DailymotionApiError, match="Invalid API response"):
            self.client.get_video("abc123")

    def test_get_video_custom_base_url(self):
        mock_get = MagicMock()
        client = DailymotionClient(base_url="https://custom.api.com", timeout=10, http_get=mock_get)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_response
        mock_get.return_value = mock_response

        client.get_video("xyz789")

        mock_get.assert_called_once_with(
            "https://custom.api.com/video/xyz789",
            timeout=10,
        )
