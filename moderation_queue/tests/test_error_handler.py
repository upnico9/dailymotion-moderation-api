from fastapi import FastAPI
from fastapi.testclient import TestClient

from domain.exceptions import (
    AuthorizationError,
    InvalidRequestError,
    InvalidStatusError,
    VideoAlreadyExistsError,
    VideoNotFoundError,
    VideoNotPendingError,
)
from infrastructure.error_handler import register_error_handlers


def _create_test_app() -> FastAPI:
    """Crée une mini app FastAPI avec les error handlers et des routes qui lèvent chaque exception."""
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/raise/video_not_found")
    def raise_video_not_found():
        raise VideoNotFoundError("Video 123 not found")

    @app.get("/raise/video_already_exists")
    def raise_video_already_exists():
        raise VideoAlreadyExistsError("Video 123 already in queue")

    @app.get("/raise/video_not_pending")
    def raise_video_not_pending():
        raise VideoNotPendingError("Video 123 is not pending")

    @app.get("/raise/invalid_status")
    def raise_invalid_status():
        raise InvalidStatusError("Invalid status 'blabla'")

    @app.get("/raise/authorization")
    def raise_authorization():
        raise AuthorizationError("Authorization header required")

    @app.get("/raise/invalid_request")
    def raise_invalid_request():
        raise InvalidRequestError("Missing field: video_id")

    @app.get("/raise/unexpected")
    def raise_unexpected():
        raise RuntimeError("Something broke")

    return app


client = TestClient(_create_test_app(), raise_server_exceptions=False)


class TestErrorHandlers:
    def test_video_not_found_returns_404(self):
        response = client.get("/raise/video_not_found")
        assert response.status_code == 404
        assert response.json() == {"error": "Video 123 not found"}

    def test_video_already_exists_returns_409(self):
        response = client.get("/raise/video_already_exists")
        assert response.status_code == 409
        assert response.json() == {"error": "Video 123 already in queue"}

    def test_video_not_pending_returns_400(self):
        response = client.get("/raise/video_not_pending")
        assert response.status_code == 400
        assert response.json() == {"error": "Video 123 is not pending"}

    def test_invalid_status_returns_400(self):
        response = client.get("/raise/invalid_status")
        assert response.status_code == 400
        assert response.json() == {"error": "Invalid status 'blabla'"}

    def test_authorization_error_returns_401(self):
        response = client.get("/raise/authorization")
        assert response.status_code == 401
        assert response.json() == {"error": "Authorization header required"}

    def test_invalid_request_returns_400(self):
        response = client.get("/raise/invalid_request")
        assert response.status_code == 400
        assert response.json() == {"error": "Missing field: video_id"}

    def test_unexpected_error_returns_500(self):
        response = client.get("/raise/unexpected")
        assert response.status_code == 500
        assert response.json() == {"error": "Internal server error"}
