import base64
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import app


def _auth_header(moderator: str) -> dict:
    encoded = base64.b64encode(moderator.encode()).decode()
    return {"Authorization": encoded}


@pytest.fixture(scope="session")
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


class TestAddVideo:
    def test_add_video_success(self, client):
        response = client.post("/add_video", json={"video_id": "vid001"})
        assert response.status_code == 201
        assert response.json() == {"video_id": "vid001"}

    def test_add_video_integer_id(self, client):
        """video_id sent as integer should be coerced to string."""
        response = client.post("/add_video", json={"video_id": 123456})
        assert response.status_code == 201
        assert response.json() == {"video_id": "123456"}

    def test_add_video_duplicate(self, client):
        client.post("/add_video", json={"video_id": "dup001"})
        response = client.post("/add_video", json={"video_id": "dup001"})
        assert response.status_code == 409
        assert "error" in response.json()

    def test_add_video_missing_body(self, client):
        response = client.post("/add_video")
        assert response.status_code == 400
        assert "error" in response.json()

    def test_add_video_missing_video_id(self, client):
        response = client.post("/add_video", json={"other": "field"})
        assert response.status_code == 400
        assert "error" in response.json()


class TestGetVideo:
    def test_get_video_success(self, client):
        client.post("/add_video", json={"video_id": "get001"})
        response = client.get("/get_video", headers=_auth_header("alice"))
        assert response.status_code == 200
        assert response.json() == {"video_id": "get001"}

    def test_get_video_no_auth(self, client):
        response = client.get("/get_video")
        assert response.status_code == 401
        assert "error" in response.json()

    def test_get_video_empty_queue(self, client):
        response = client.get("/get_video", headers=_auth_header("bob"))
        assert response.status_code == 404
        assert "error" in response.json()

    def test_get_video_idempotent(self, client):
        client.post("/add_video", json={"video_id": "idem001"})
        r1 = client.get("/get_video", headers=_auth_header("carol"))
        r2 = client.get("/get_video", headers=_auth_header("carol"))
        assert r1.json() == r2.json()

    def test_get_video_different_moderators(self, client):
        client.post("/add_video", json={"video_id": "diff001"})
        client.post("/add_video", json={"video_id": "diff002"})
        r1 = client.get("/get_video", headers=_auth_header("dave"))
        r2 = client.get("/get_video", headers=_auth_header("eve"))
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json()["video_id"] != r2.json()["video_id"]


class TestFlagVideo:
    def _add_and_assign(self, client, video_id, moderator):
        client.post("/add_video", json={"video_id": video_id})
        client.get("/get_video", headers=_auth_header(moderator))

    def test_flag_video_spam(self, client):
        self._add_and_assign(client, "flag001", "frank")
        response = client.post(
            "/flag_video",
            json={"video_id": "flag001", "status": "spam"},
            headers=_auth_header("frank"),
        )
        assert response.status_code == 200
        assert response.json() == {"video_id": "flag001", "status": "spam"}

    def test_flag_video_not_spam(self, client):
        self._add_and_assign(client, "flag002", "grace")
        response = client.post(
            "/flag_video",
            json={"video_id": "flag002", "status": "not spam"},
            headers=_auth_header("grace"),
        )
        assert response.status_code == 200
        assert response.json() == {"video_id": "flag002", "status": "not spam"}

    def test_flag_video_not_found(self, client):
        response = client.post(
            "/flag_video",
            json={"video_id": "nonexistent", "status": "spam"},
            headers=_auth_header("heidi"),
        )
        assert response.status_code == 404

    def test_flag_video_not_assigned_to_moderator(self, client):
        self._add_and_assign(client, "flag003", "ivan")
        response = client.post(
            "/flag_video",
            json={"video_id": "flag003", "status": "spam"},
            headers=_auth_header("judy"),
        )
        assert response.status_code == 403

    def test_flag_video_invalid_status(self, client):
        self._add_and_assign(client, "flag004", "karl")
        response = client.post(
            "/flag_video",
            json={"video_id": "flag004", "status": "invalid"},
            headers=_auth_header("karl"),
        )
        assert response.status_code == 400

    def test_flag_video_already_flagged(self, client):
        self._add_and_assign(client, "flag005", "liam")
        client.post(
            "/flag_video",
            json={"video_id": "flag005", "status": "spam"},
            headers=_auth_header("liam"),
        )
        response = client.post(
            "/flag_video",
            json={"video_id": "flag005", "status": "not spam"},
            headers=_auth_header("liam"),
        )
        assert response.status_code == 400

    def test_flag_video_no_auth(self, client):
        response = client.post(
            "/flag_video",
            json={"video_id": "flag006", "status": "spam"},
        )
        assert response.status_code == 401

    def test_flag_video_missing_body(self, client):
        response = client.post("/flag_video", headers=_auth_header("mallory"))
        assert response.status_code == 400


class TestStats:
    def test_stats_empty(self, client):
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_pending_videos"] == 0
        assert data["total_spam_videos"] == 0
        assert data["total_not_spam_videos"] == 0

    def test_stats_mixed(self, client):
        client.post("/add_video", json={"video_id": "stat001"})
        client.post("/add_video", json={"video_id": "stat002"})
        client.post("/add_video", json={"video_id": "stat003"})

        client.get("/get_video", headers=_auth_header("nina"))
        client.post(
            "/flag_video",
            json={"video_id": "stat001", "status": "spam"},
            headers=_auth_header("nina"),
        )

        client.get("/get_video", headers=_auth_header("oscar"))
        client.post(
            "/flag_video",
            json={"video_id": "stat002", "status": "not spam"},
            headers=_auth_header("oscar"),
        )

        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_pending_videos"] == 1
        assert data["total_spam_videos"] == 1
        assert data["total_not_spam_videos"] == 1


class TestLogVideo:
    def test_log_video_after_add_and_flag(self, client):
        client.post("/add_video", json={"video_id": "log001"})
        client.get("/get_video", headers=_auth_header("pat"))
        client.post(
            "/flag_video",
            json={"video_id": "log001", "status": "spam"},
            headers=_auth_header("pat"),
        )

        response = client.get("/log_video/log001")
        assert response.status_code == 200
        logs = response.json()
        assert len(logs) == 3

        assert logs[0]["status"] == "pending"
        assert logs[0]["moderator"] is None

        assert logs[1]["status"] == "pending"
        assert logs[1]["moderator"] == "pat"

        assert logs[2]["status"] == "spam"
        assert logs[2]["moderator"] == "pat"

    def test_log_video_empty(self, client):
        response = client.get("/log_video/unknown")
        assert response.status_code == 200
        assert response.json() == []
