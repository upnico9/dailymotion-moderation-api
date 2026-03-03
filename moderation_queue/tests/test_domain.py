from datetime import datetime

import pytest

from domain.value_objects import ModerationStatus
from domain.entities import Video, VideoLog

class TestModerationStatus:
    def test_values(self):
        assert ModerationStatus.PENDING.value == "pending"
        assert ModerationStatus.SPAM.value == "spam"
        assert ModerationStatus.NOT_SPAM.value == "not spam"

    def test_from_string_pending(self):
        assert ModerationStatus.from_string("pending") == ModerationStatus.PENDING

    def test_from_string_spam(self):
        assert ModerationStatus.from_string("spam") == ModerationStatus.SPAM

    def test_from_string_not_spam(self):
        assert ModerationStatus.from_string("not spam") == ModerationStatus.NOT_SPAM

    def test_from_string_invalid_raises(self):
        with pytest.raises(ValueError, match="Invalid status 'blabla'"):
            ModerationStatus.from_string("blabla")

    def test_from_string_empty_raises(self):
        with pytest.raises(ValueError):
            ModerationStatus.from_string("")


# ---------------------------------------------------------------------------
# Video
# ---------------------------------------------------------------------------

def _make_video(
    video_id: str = "123456",
    status: ModerationStatus = ModerationStatus.PENDING,
    assigned_moderator: str | None = None,
) -> Video:
    now = datetime(2026, 1, 1, 12, 0, 0)
    return Video(
        video_id=video_id,
        status=status,
        assigned_moderator=assigned_moderator,
        created_at=now,
        updated_at=now,
    )


class TestVideo:
    def test_create_pending_video(self):
        video = _make_video()
        assert video.video_id == "123456"
        assert video.status == ModerationStatus.PENDING
        assert video.assigned_moderator is None
        assert video.is_pending() is True

    def test_assign_to_moderator(self):
        video = _make_video()
        video.assign_to("john.doe")
        assert video.assigned_moderator == "john.doe"

    def test_assign_to_replaces_previous(self):
        video = _make_video(assigned_moderator="alice")
        video.assign_to("bob")
        assert video.assigned_moderator == "bob"

    def test_flag_spam(self):
        video = _make_video(assigned_moderator="john.doe")
        video.flag(ModerationStatus.SPAM)
        assert video.status == ModerationStatus.SPAM
        assert video.is_pending() is False

    def test_flag_not_spam(self):
        video = _make_video(assigned_moderator="john.doe")
        video.flag(ModerationStatus.NOT_SPAM)
        assert video.status == ModerationStatus.NOT_SPAM

    def test_flag_already_flagged_raises(self):
        video = _make_video(status=ModerationStatus.SPAM)
        with pytest.raises(ValueError, match="expected 'pending'"):
            video.flag(ModerationStatus.NOT_SPAM)

    def test_flag_not_spam_then_flag_again_raises(self):
        video = _make_video()
        video.flag(ModerationStatus.NOT_SPAM)
        with pytest.raises(ValueError, match="expected 'pending'"):
            video.flag(ModerationStatus.SPAM)

    def test_is_pending_true(self):
        video = _make_video()
        assert video.is_pending() is True

    def test_is_pending_false_after_flag(self):
        video = _make_video()
        video.flag(ModerationStatus.SPAM)
        assert video.is_pending() is False

    def test_repr(self):
        video = _make_video()
        r = repr(video)
        assert "123456" in r
        assert "pending" in r


class TestVideoLog:
    def test_create_log(self):
        now = datetime(2026, 1, 1, 12, 0, 0)
        log = VideoLog(
            id=1,
            video_id="123456",
            status="pending",
            moderator=None,
            created_at=now,
        )
        assert log.id == 1
        assert log.video_id == "123456"
        assert log.status == "pending"
        assert log.moderator is None
        assert log.created_at == now

    def test_create_log_with_moderator(self):
        now = datetime(2026, 1, 1, 13, 0, 0)
        log = VideoLog(
            id=2,
            video_id="123456",
            status="spam",
            moderator="john.doe",
            created_at=now,
        )
        assert log.moderator == "john.doe"
        assert log.status == "spam"

    def test_repr(self):
        now = datetime(2026, 1, 1, 12, 0, 0)
        log = VideoLog(id=1, video_id="123456", status="pending", moderator=None, created_at=now)
        r = repr(log)
        assert "123456" in r
        assert "pending" in r

    def test_video_lifecycle_spam(self):
        t1 = datetime(2026, 1, 1, 12, 0, 0)
        t2 = datetime(2026, 1, 1, 12, 5, 0)
        t3 = datetime(2026, 1, 1, 12, 10, 0)

        video = _make_video(video_id="789")

        log_created = VideoLog(id=1, video_id=video.video_id, status=video.status.value, moderator=video.assigned_moderator, created_at=t1)
        assert log_created.status == "pending"
        assert log_created.moderator is None

        video.assign_to("john.doe")
        log_assigned = VideoLog(id=2, video_id=video.video_id, status=video.status.value, moderator=video.assigned_moderator, created_at=t2)
        assert log_assigned.status == "pending"
        assert log_assigned.moderator == "john.doe"

        video.flag(ModerationStatus.SPAM)
        log_flagged = VideoLog(id=3, video_id=video.video_id, status=video.status.value, moderator=video.assigned_moderator, created_at=t3)
        assert log_flagged.status == "spam"
        assert log_flagged.moderator == "john.doe"

        logs = [log_created, log_assigned, log_flagged]
        assert len(logs) == 3
        assert logs[0].created_at < logs[1].created_at < logs[2].created_at

    def test_video_lifecycle_not_spam(self):
        t1 = datetime(2026, 1, 1, 14, 0, 0)
        t2 = datetime(2026, 1, 1, 14, 3, 0)
        t3 = datetime(2026, 1, 1, 14, 8, 0)

        video = _make_video(video_id="999")

        log_created = VideoLog(id=10, video_id=video.video_id, status=video.status.value, moderator=video.assigned_moderator, created_at=t1)
        assert log_created.status == "pending"
        assert log_created.moderator is None

        video.assign_to("alice")
        log_assigned = VideoLog(id=11, video_id=video.video_id, status=video.status.value, moderator=video.assigned_moderator, created_at=t2)
        assert log_assigned.moderator == "alice"

        video.flag(ModerationStatus.NOT_SPAM)
        log_flagged = VideoLog(id=12, video_id=video.video_id, status=video.status.value, moderator=video.assigned_moderator, created_at=t3)
        assert log_flagged.status == "not spam"
        assert log_flagged.moderator == "alice"

        logs = [log_created, log_assigned, log_flagged]
        assert logs[0].created_at < logs[1].created_at < logs[2].created_at
