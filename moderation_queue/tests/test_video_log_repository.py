import time

import pytest

from repositories.video_repository import VideoRepository
from repositories.video_log_repository import VideoLogRepository


@pytest.fixture
def video_repo(db_pool):
    return VideoRepository(db_pool)


@pytest.fixture
def log_repo(db_pool):
    return VideoLogRepository(db_pool)


class TestCreate:
    def test_create_log(self, video_repo, log_repo):
        video_repo.add("v001")
        log = log_repo.create("v001", "pending")
        assert log.video_id == "v001"
        assert log.status == "pending"
        assert log.moderator is None
        assert log.created_at is not None

    def test_create_log_with_moderator(self, video_repo, log_repo):
        video_repo.add("v001")
        log = log_repo.create("v001", "spam", "john.doe")
        assert log.status == "spam"
        assert log.moderator == "john.doe"

    def test_create_log_auto_increments_id(self, video_repo, log_repo):
        video_repo.add("v001")
        log1 = log_repo.create("v001", "pending")
        log2 = log_repo.create("v001", "spam", "john.doe")
        assert log2.id > log1.id

    def test_create_log_fails_without_video(self, log_repo):
        with pytest.raises(Exception):
            log_repo.create("unknown", "pending")


class TestGetByVideoId:
    def test_returns_logs_in_chronological_order(self, video_repo, log_repo):
        video_repo.add("v001")
        log_repo.create("v001", "pending")
        time.sleep(0.01)
        log_repo.create("v001", "spam", "john.doe")

        logs = log_repo.get_by_video_id("v001")
        assert len(logs) == 2
        assert logs[0].status == "pending"
        assert logs[1].status == "spam"
        assert logs[0].created_at <= logs[1].created_at

    def test_empty_returns_empty_list(self, video_repo, log_repo):
        video_repo.add("v001")
        logs = log_repo.get_by_video_id("v001")
        assert logs == []

    def test_unknown_video_returns_empty_list(self, log_repo):
        logs = log_repo.get_by_video_id("unknown")
        assert logs == []

    def test_does_not_return_other_video_logs(self, video_repo, log_repo):
        video_repo.add("v001")
        video_repo.add("v002")
        log_repo.create("v001", "pending")
        log_repo.create("v002", "pending")

        logs = log_repo.get_by_video_id("v001")
        assert len(logs) == 1
        assert logs[0].video_id == "v001"


class TestLifecycle:
    def test_full_moderation_lifecycle(self, video_repo, log_repo):
        video_repo.add("v001")

        log_repo.create("v001", "pending")
        time.sleep(0.01)
        log_repo.create("v001", "pending", "john.doe")
        time.sleep(0.01)
        log_repo.create("v001", "spam", "john.doe")

        logs = log_repo.get_by_video_id("v001")
        assert len(logs) == 3

        assert logs[0].status == "pending"
        assert logs[0].moderator is None

        assert logs[1].status == "pending"
        assert logs[1].moderator == "john.doe"

        assert logs[2].status == "spam"
        assert logs[2].moderator == "john.doe"

        assert logs[0].created_at < logs[1].created_at < logs[2].created_at
