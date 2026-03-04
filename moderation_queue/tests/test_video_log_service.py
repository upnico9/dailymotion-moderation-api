from datetime import datetime
from unittest.mock import MagicMock

import pytest

from domain.entities import VideoLog
from services.video_log_service import VideoLogService

NOW = datetime(2026, 1, 1, 12, 0, 0)


def _make_log(
    id: int = 1,
    video_id: str = "abc123",
    status: str = "pending",
    moderator: str | None = None,
) -> VideoLog:
    return VideoLog(
        id=id,
        video_id=video_id,
        status=status,
        moderator=moderator,
        created_at=NOW,
    )


@pytest.fixture
def video_log_repo():
    return MagicMock()


@pytest.fixture
def service(video_log_repo):
    return VideoLogService(video_log_repo)


class TestLogAdded:
    def test_creates_pending_log_without_moderator(self, service, video_log_repo):
        service.log_added("abc123")

        video_log_repo.create.assert_called_once_with("abc123", "pending", None)


class TestLogAssigned:
    def test_creates_pending_log_with_moderator(self, service, video_log_repo):
        service.log_assigned("abc123", "alice")

        video_log_repo.create.assert_called_once_with("abc123", "pending", "alice")


class TestLogFlagged:
    def test_creates_log_with_status_and_moderator(self, service, video_log_repo):
        service.log_flagged("abc123", "spam", "alice")

        video_log_repo.create.assert_called_once_with("abc123", "spam", "alice")

    def test_creates_log_not_spam(self, service, video_log_repo):
        service.log_flagged("abc123", "not spam", "bob")

        video_log_repo.create.assert_called_once_with("abc123", "not spam", "bob")


class TestGetVideoLogs:
    def test_returns_formatted_logs(self, service, video_log_repo):
        logs = [
            _make_log(id=1, status="pending", moderator=None),
            _make_log(id=2, status="pending", moderator="alice"),
            _make_log(id=3, status="spam", moderator="alice"),
        ]
        video_log_repo.get_by_video_id.return_value = logs

        result = service.get_video_logs("abc123")

        assert len(result) == 3
        assert result[0] == {
            "date": NOW.isoformat(),
            "status": "pending",
            "moderator": None,
        }
        assert result[1] == {
            "date": NOW.isoformat(),
            "status": "pending",
            "moderator": "alice",
        }
        assert result[2] == {
            "date": NOW.isoformat(),
            "status": "spam",
            "moderator": "alice",
        }
        video_log_repo.get_by_video_id.assert_called_once_with("abc123")

    def test_returns_empty_list(self, service, video_log_repo):
        video_log_repo.get_by_video_id.return_value = []

        result = service.get_video_logs("unknown")

        assert result == []

    def test_single_log_entry(self, service, video_log_repo):
        video_log_repo.get_by_video_id.return_value = [
            _make_log(id=1, status="pending", moderator=None)
        ]

        result = service.get_video_logs("abc123")

        assert len(result) == 1
        assert result[0]["status"] == "pending"
        assert result[0]["moderator"] is None

    def test_log_with_moderator(self, service, video_log_repo):
        video_log_repo.get_by_video_id.return_value = [
            _make_log(id=1, status="pending", moderator=None),
            _make_log(id=1, status="pending", moderator="bob")
        ]

        result = service.get_video_logs("abc123")

        assert result[1]["status"] == "pending"
        assert result[1]["moderator"] == "bob"
