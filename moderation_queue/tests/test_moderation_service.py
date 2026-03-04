from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from psycopg2.errors import UniqueViolation

from domain.entities import Video, VideoLog
from domain.events import VideoAdded, VideoAssigned, VideoFlagged
from domain.exceptions import (
    ForbiddenError,
    InvalidStatusError,
    VideoAlreadyExistsError,
    VideoNotFoundError,
    VideoNotPendingError,
)
from domain.value_objects import ModerationStatus
from infrastructure.event_dispatcher import EventDispatcher
from services.moderation_service import ModerationService
from services.video_log_service import VideoLogService


NOW = datetime(2026, 1, 1, 12, 0, 0)


def _make_video(
    video_id: str = "abc123",
    status: ModerationStatus = ModerationStatus.PENDING,
    assigned_moderator: str | None = None,
) -> Video:
    return Video(
        video_id=video_id,
        status=status,
        assigned_moderator=assigned_moderator,
        created_at=NOW,
        updated_at=NOW,
    )


@pytest.fixture
def video_repo():
    return MagicMock()


@pytest.fixture
def video_log_service():
    return MagicMock(spec=VideoLogService)


@pytest.fixture
def service(video_repo, video_log_service):
    """Service with a real EventDispatcher so listeners actually fire."""
    dispatcher = EventDispatcher()
    return ModerationService(video_repo, video_log_service, dispatcher)


class TestAddVideo:
    def test_creates_video(self, service, video_repo):
        video = _make_video()
        video_repo.add.return_value = video

        result = service.add_video("abc123")

        assert result == video
        video_repo.add.assert_called_once_with("abc123")

    def test_dispatches_event_and_creates_log(self, service, video_repo, video_log_service):
        video_repo.add.return_value = _make_video()

        service.add_video("abc123")

        video_log_service.log_added.assert_called_once_with("abc123")

    def test_duplicate_raises_already_exists(self, service, video_repo):

        video_repo.add.side_effect = UniqueViolation("duplicate key")

        with pytest.raises(VideoAlreadyExistsError, match="already in the queue"):
            service.add_video("abc123")


class TestGetVideo:
    def test_returns_already_assigned_video(self, service, video_repo, video_log_service):
        video = _make_video(assigned_moderator="alice")
        video_repo.get_assigned.return_value = video

        result = service.get_video("alice")

        assert result == video
        video_repo.get_assigned.assert_called_once_with("alice")
        video_repo.get_next_pending.assert_not_called()
        video_log_service.log_assigned.assert_not_called()

    def test_assigns_next_pending_and_creates_log(self, service, video_repo, video_log_service):
        assigned_video = _make_video(assigned_moderator="alice")

        video_repo.get_assigned.return_value = None
        video_repo.get_next_pending_and_assign.return_value = assigned_video

        result = service.get_video("alice")

        assert result == assigned_video
        video_repo.get_next_pending_and_assign.assert_called_once_with("alice")
        video_log_service.log_assigned.assert_called_once_with("abc123", "alice")

    def test_returns_none_when_queue_empty(self, service, video_repo, video_log_service):
        video_repo.get_assigned.return_value = None
        video_repo.get_next_pending_and_assign.return_value = None

        result = service.get_video("alice")

        assert result is None
        video_log_service.log_assigned.assert_not_called()


class TestFlagVideo:
    def test_flag_spam_success(self, service, video_repo, video_log_service):
        video = _make_video(assigned_moderator="alice")
        flagged_video = _make_video(status=ModerationStatus.SPAM, assigned_moderator="alice")

        video_repo.get_by_id.side_effect = [video, flagged_video]

        result = service.flag_video("abc123", "spam", "alice")

        assert result.status == ModerationStatus.SPAM
        video_repo.flag.assert_called_once_with("abc123", "spam")
        video_log_service.log_flagged.assert_called_once_with("abc123", "spam", "alice")

    def test_flag_not_spam_success(self, service, video_repo, video_log_service):
        video = _make_video(assigned_moderator="bob")
        flagged_video = _make_video(status=ModerationStatus.NOT_SPAM, assigned_moderator="bob")

        video_repo.get_by_id.side_effect = [video, flagged_video]

        result = service.flag_video("abc123", "not spam", "bob")

        assert result.status == ModerationStatus.NOT_SPAM
        video_repo.flag.assert_called_once_with("abc123", "not spam")
        video_log_service.log_flagged.assert_called_once_with("abc123", "not spam", "bob")

    def test_video_not_found_raises(self, service, video_repo, video_log_service):
        video_repo.get_by_id.return_value = None

        with pytest.raises(VideoNotFoundError, match="not found"):
            service.flag_video("unknown", "spam", "alice")

        video_repo.flag.assert_not_called()
        video_log_service.log_flagged.assert_not_called()

    def test_not_assigned_to_moderator_raises(self, service, video_repo, video_log_service):
        video = _make_video(assigned_moderator="bob")
        video_repo.get_by_id.return_value = video

        with pytest.raises(ForbiddenError, match="not assigned to alice"):
            service.flag_video("abc123", "spam", "alice")

        video_repo.flag.assert_not_called()
        video_log_service.log_flagged.assert_not_called()

    def test_unassigned_video_raises(self, service, video_repo, video_log_service):
        video = _make_video(assigned_moderator=None)
        video_repo.get_by_id.return_value = video

        with pytest.raises(ForbiddenError, match="not assigned to alice"):
            service.flag_video("abc123", "spam", "alice")

        video_repo.flag.assert_not_called()
        video_log_service.log_flagged.assert_not_called()

    def test_already_flagged_raises(self, service, video_repo, video_log_service):
        video = _make_video(status=ModerationStatus.SPAM, assigned_moderator="alice")
        video_repo.get_by_id.return_value = video

        with pytest.raises(VideoNotPendingError, match="not pending"):
            service.flag_video("abc123", "not spam", "alice")

        video_repo.flag.assert_not_called()
        video_log_service.log_flagged.assert_not_called()

    def test_invalid_status_raises(self, service, video_repo, video_log_service):
        video = _make_video(assigned_moderator="alice")
        video_repo.get_by_id.return_value = video

        with pytest.raises(InvalidStatusError, match="Invalid status"):
            service.flag_video("abc123", "invalid", "alice")

        video_repo.flag.assert_not_called()
        video_log_service.log_flagged.assert_not_called()

class TestGetStats:
    def test_returns_counts(self, service, video_repo):
        video_repo.count_by_status.return_value = {
            "total_pending_videos": 5,
            "total_spam_videos": 3,
            "total_not_spam_videos": 2,
        }

        result = service.get_stats()

        assert result == {
            "total_pending_videos": 5,
            "total_spam_videos": 3,
            "total_not_spam_videos": 2,
        }
        video_repo.count_by_status.assert_called_once()

    def test_returns_zeros_when_empty(self, service, video_repo):
        video_repo.count_by_status.return_value = {
            "total_pending_videos": 0,
            "total_spam_videos": 0,
            "total_not_spam_videos": 0,
        }

        result = service.get_stats()

        assert result["total_pending_videos"] == 0
        assert result["total_spam_videos"] == 0
        assert result["total_not_spam_videos"] == 0
