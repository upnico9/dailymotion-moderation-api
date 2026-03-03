import time

import pytest

from domain.value_objects import ModerationStatus
from repositories.video_repository import VideoRepository


@pytest.fixture
def video_repo(db_pool):
    return VideoRepository(db_pool)


class TestAdd:
    def test_add_video(self, video_repo):
        video = video_repo.add("v001")
        assert video.video_id == "v001"
        assert video.status == ModerationStatus.PENDING
        assert video.assigned_moderator is None

    def test_add_sets_timestamps(self, video_repo):
        video = video_repo.add("v001")
        assert video.created_at is not None
        assert video.updated_at is not None
        assert video.created_at == video.updated_at

    def test_add_duplicate_raises(self, video_repo):
        video_repo.add("v001")
        with pytest.raises(Exception):
            video_repo.add("v001")


class TestGetById:
    def test_existing(self, video_repo):
        video_repo.add("v001")
        video = video_repo.get_by_id("v001")
        assert video is not None
        assert video.video_id == "v001"

    def test_not_found(self, video_repo):
        assert video_repo.get_by_id("unknown") is None


class TestGetNextPending:
    def test_fifo_order(self, video_repo):
        video_repo.add("v001")
        video_repo.add("v002")
        video_repo.add("v003")
        video = video_repo.get_next_pending()
        assert video.video_id == "v001"

    def test_skips_assigned(self, video_repo):
        video_repo.add("v001")
        video_repo.assign("v001", "john.doe")
        video_repo.add("v002")
        video = video_repo.get_next_pending()
        assert video.video_id == "v002"

    def test_skips_flagged(self, video_repo):
        video_repo.add("v001")
        video_repo.flag("v001", "spam")
        video = video_repo.get_next_pending()
        assert video is None

    def test_returns_second_when_first_flagged(self, video_repo):
        video_repo.add("v001")
        video_repo.add("v002")
        video_repo.flag("v001", "spam")
        video = video_repo.get_next_pending()
        assert video.video_id == "v002"

    def test_all_assigned_returns_none(self, video_repo):
        video_repo.add("v001")
        video_repo.add("v002")
        video_repo.assign("v001", "alice")
        video_repo.assign("v002", "bob")
        assert video_repo.get_next_pending() is None

    def test_empty_queue(self, video_repo):
        assert video_repo.get_next_pending() is None


class TestAssign:
    def test_assign_and_get_assigned(self, video_repo):
        video_repo.add("v001")
        video_repo.assign("v001", "john.doe")
        video = video_repo.get_assigned("john.doe")
        assert video is not None
        assert video.video_id == "v001"
        assert video.assigned_moderator == "john.doe"

    def test_assign_updates_updated_at(self, video_repo):
        video = video_repo.add("v001")
        original_updated_at = video.updated_at
        time.sleep(0.01)
        video_repo.assign("v001", "john.doe")
        updated_video = video_repo.get_by_id("v001")
        assert updated_video.updated_at > original_updated_at
        assert updated_video.created_at == video.created_at

    def test_get_assigned_no_match(self, video_repo):
        video_repo.add("v001")
        assert video_repo.get_assigned("john.doe") is None

    def test_get_assigned_returns_none_after_flag(self, video_repo):
        video_repo.add("v001")
        video_repo.assign("v001", "john.doe")
        video_repo.flag("v001", "spam")
        assert video_repo.get_assigned("john.doe") is None


class TestFlag:
    def test_flag_updates_status(self, video_repo):
        video_repo.add("v001")
        video_repo.flag("v001", "spam")
        video = video_repo.get_by_id("v001")
        assert video.status == ModerationStatus.SPAM

    def test_flag_not_spam(self, video_repo):
        video_repo.add("v001")
        video_repo.flag("v001", "not spam")
        video = video_repo.get_by_id("v001")
        assert video.status == ModerationStatus.NOT_SPAM

    def test_flag_updates_updated_at(self, video_repo):
        video = video_repo.add("v001")
        original_updated_at = video.updated_at
        time.sleep(0.01)
        video_repo.flag("v001", "spam")
        updated_video = video_repo.get_by_id("v001")
        assert updated_video.updated_at > original_updated_at
        assert updated_video.created_at == video.created_at

    def test_flag_does_not_affect_other_videos(self, video_repo):
        video_repo.add("v001")
        video_repo.add("v002")
        video_repo.flag("v001", "spam")
        other = video_repo.get_by_id("v002")
        assert other.status == ModerationStatus.PENDING


class TestCountByStatus:
    def test_empty(self, video_repo):
        counts = video_repo.count_by_status()
        assert counts == {
            "total_pending_videos": 0,
            "total_spam_videos": 0,
            "total_not_spam_videos": 0,
        }

    def test_mixed_statuses(self, video_repo):
        video_repo.add("v001")
        video_repo.add("v002")
        video_repo.add("v003")
        video_repo.flag("v002", "spam")
        video_repo.flag("v003", "not spam")

        counts = video_repo.count_by_status()
        assert counts["total_pending_videos"] == 1
        assert counts["total_spam_videos"] == 1
        assert counts["total_not_spam_videos"] == 1

    def test_multiple_same_status(self, video_repo):
        video_repo.add("v001")
        video_repo.add("v002")
        video_repo.add("v003")
        video_repo.flag("v001", "spam")
        video_repo.flag("v002", "spam")

        counts = video_repo.count_by_status()
        assert counts["total_pending_videos"] == 1
        assert counts["total_spam_videos"] == 2
        assert counts["total_not_spam_videos"] == 0


class TestSkipLocked:
    def test_concurrent_get_next_pending_skips_locked_row(self, video_repo, db_pool):
        """
            Simulate two concurrent operations:
            Transaction 1 locks the first video without committing
            Transaction 2 must skip the locked row and take the second video
        """
        video_repo.add("v001")
        video_repo.add("v002")

        conn1 = db_pool.getconn()
        conn1.autocommit = False
        cur1 = conn1.cursor()
        cur1.execute(
            """
            SELECT * FROM videos_queue
            WHERE status = 'pending' AND assigned_moderator IS NULL
            ORDER BY created_at ASC
            LIMIT 1
            FOR UPDATE SKIP LOCKED
            """
        )
        row1 = cur1.fetchone()
        assert row1[0] == "v001" 

        conn2 = db_pool.getconn()
        conn2.autocommit = False
        cur2 = conn2.cursor()
        cur2.execute(
            """
            SELECT * FROM videos_queue
            WHERE status = 'pending' AND assigned_moderator IS NULL
            ORDER BY created_at ASC
            LIMIT 1
            FOR UPDATE SKIP LOCKED
            """
        )
        row2 = cur2.fetchone()
        assert row2[0] == "v002"

        conn1.rollback()
        conn2.rollback()
        cur1.close()
        cur2.close()
        db_pool.putconn(conn1)
        db_pool.putconn(conn2)
