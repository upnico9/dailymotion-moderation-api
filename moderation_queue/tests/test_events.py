from datetime import datetime

import pytest

from domain.events import VideoAdded, VideoAssigned, VideoFlagged
from domain.value_objects import ModerationStatus
from infrastructure.event_dispatcher import EventDispatcher

NOW = datetime(2026, 1, 1, 12, 0, 0)


class TestVideoAdded:
    def test_creation(self):
        event = VideoAdded(video_id="abc123", occurred_at=NOW)
        assert event.video_id == "abc123"
        assert event.occurred_at == NOW

    def test_frozen(self):
        event = VideoAdded(video_id="abc123", occurred_at=NOW)
        with pytest.raises(AttributeError):
            event.video_id = "other"

    def test_equality(self):
        e1 = VideoAdded(video_id="abc123", occurred_at=NOW)
        e2 = VideoAdded(video_id="abc123", occurred_at=NOW)
        assert e1 == e2

    def test_inequality_different_id(self):
        e1 = VideoAdded(video_id="abc123", occurred_at=NOW)
        e2 = VideoAdded(video_id="xyz789", occurred_at=NOW)
        assert e1 != e2


class TestVideoAssigned:
    def test_creation(self):
        event = VideoAssigned(video_id="abc123", moderator="alice", occurred_at=NOW)
        assert event.video_id == "abc123"
        assert event.moderator == "alice"
        assert event.occurred_at == NOW

    def test_frozen(self):
        event = VideoAssigned(video_id="abc123", moderator="alice", occurred_at=NOW)
        with pytest.raises(AttributeError):
            event.moderator = "bob"

    def test_equality(self):
        e1 = VideoAssigned(video_id="abc123", moderator="alice", occurred_at=NOW)
        e2 = VideoAssigned(video_id="abc123", moderator="alice", occurred_at=NOW)
        assert e1 == e2

    def test_inequality_different_moderator(self):
        e1 = VideoAssigned(video_id="abc123", moderator="alice", occurred_at=NOW)
        e2 = VideoAssigned(video_id="abc123", moderator="bob", occurred_at=NOW)
        assert e1 != e2


class TestVideoFlagged:
    def test_creation_spam(self):
        event = VideoFlagged(
            video_id="abc123",
            status=ModerationStatus.SPAM,
            moderator="alice",
            occurred_at=NOW,
        )
        assert event.video_id == "abc123"
        assert event.status == ModerationStatus.SPAM
        assert event.moderator == "alice"
        assert event.occurred_at == NOW

    def test_creation_not_spam(self):
        event = VideoFlagged(
            video_id="abc123",
            status=ModerationStatus.NOT_SPAM,
            moderator="bob",
            occurred_at=NOW,
        )
        assert event.status == ModerationStatus.NOT_SPAM
        assert event.moderator == "bob"

    def test_frozen(self):
        event = VideoFlagged(
            video_id="abc123",
            status=ModerationStatus.SPAM,
            moderator="alice",
            occurred_at=NOW,
        )
        with pytest.raises(AttributeError):
            event.status = ModerationStatus.NOT_SPAM

    def test_equality(self):
        kwargs = dict(
            video_id="abc123",
            status=ModerationStatus.SPAM,
            moderator="alice",
            occurred_at=NOW,
        )
        assert VideoFlagged(**kwargs) == VideoFlagged(**kwargs)

    def test_inequality_different_status(self):
        base = dict(video_id="abc123", moderator="alice", occurred_at=NOW)
        e1 = VideoFlagged(status=ModerationStatus.SPAM, **base)
        e2 = VideoFlagged(status=ModerationStatus.NOT_SPAM, **base)
        assert e1 != e2


class TestEventDispatcher:
    def test_dispatch_calls_registered_listener(self):
        dispatcher = EventDispatcher()
        received = []
        dispatcher.listen(VideoAdded, lambda e: received.append(e))

        event = VideoAdded(video_id="v1", occurred_at=NOW)
        dispatcher.dispatch(event)

        assert received == [event]

    def test_dispatch_multiple_listeners(self):
        dispatcher = EventDispatcher()
        log_a, log_b = [], []
        dispatcher.listen(VideoAdded, lambda e: log_a.append(e))
        dispatcher.listen(VideoAdded, lambda e: log_b.append(e))

        event = VideoAdded(video_id="v1", occurred_at=NOW)
        dispatcher.dispatch(event)

        assert log_a == [event]
        assert log_b == [event]

    def test_dispatch_only_matching_type(self):
        dispatcher = EventDispatcher()
        added_log, assigned_log = [], []
        dispatcher.listen(VideoAdded, lambda e: added_log.append(e))
        dispatcher.listen(VideoAssigned, lambda e: assigned_log.append(e))

        event = VideoAdded(video_id="v1", occurred_at=NOW)
        dispatcher.dispatch(event)

        assert len(added_log) == 1
        assert len(assigned_log) == 0

    def test_dispatch_no_listeners_does_nothing(self):
        dispatcher = EventDispatcher()
        event = VideoAdded(video_id="v1", occurred_at=NOW)
        dispatcher.dispatch(event)

    def test_dispatch_different_event_types(self):
        dispatcher = EventDispatcher()
        added_log, flagged_log = [], []
        dispatcher.listen(VideoAdded, lambda e: added_log.append(e))
        dispatcher.listen(VideoFlagged, lambda e: flagged_log.append(e))

        added = VideoAdded(video_id="v1", occurred_at=NOW)
        flagged = VideoFlagged(
            video_id="v1",
            status=ModerationStatus.SPAM,
            moderator="alice",
            occurred_at=NOW,
        )
        dispatcher.dispatch(added)
        dispatcher.dispatch(flagged)

        assert added_log == [added]
        assert flagged_log == [flagged]

    def test_listener_receives_correct_event_data(self):
        dispatcher = EventDispatcher()
        received = []
        dispatcher.listen(VideoAssigned, lambda e: received.append(e))

        event = VideoAssigned(video_id="v42", moderator="charlie", occurred_at=NOW)
        dispatcher.dispatch(event)

        assert received[0].video_id == "v42"
        assert received[0].moderator == "charlie"

    def test_dispatch_preserves_listener_order(self):
        dispatcher = EventDispatcher()
        order = []
        dispatcher.listen(VideoAdded, lambda e: order.append("first"))
        dispatcher.listen(VideoAdded, lambda e: order.append("second"))
        dispatcher.listen(VideoAdded, lambda e: order.append("third"))

        dispatcher.dispatch(VideoAdded(video_id="v1", occurred_at=NOW))

        assert order == ["first", "second", "third"]

    def test_multiple_dispatches(self):
        dispatcher = EventDispatcher()
        count = []
        dispatcher.listen(VideoAdded, lambda e: count.append(1))

        dispatcher.dispatch(VideoAdded(video_id="v1", occurred_at=NOW))
        dispatcher.dispatch(VideoAdded(video_id="v2", occurred_at=NOW))

        assert len(count) == 2
