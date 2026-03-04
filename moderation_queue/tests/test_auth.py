import base64

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from domain.exceptions import AuthorizationError
from infrastructure.error_handler import register_error_handlers
from middleware.auth import decode_authorization, get_current_moderator


class TestDecodeAuthorization:
    def test_valid_base64(self):
        encoded = base64.b64encode(b"alice").decode()
        assert decode_authorization(encoded) == "alice"

    def test_valid_base64_with_spaces(self):
        encoded = base64.b64encode(b"  bob  ").decode()
        assert decode_authorization(encoded) == "bob"

    def test_unicode_moderator(self):
        encoded = base64.b64encode("hélo".encode("utf-8")).decode()
        assert decode_authorization(encoded) == "hélo"

    def test_invalid_base64_raises(self):
        with pytest.raises(AuthorizationError, match="Invalid authorization header"):
            decode_authorization("!!!not-base64!!!")

    def test_empty_string_raises(self):
        encoded = base64.b64encode(b"").decode()
        with pytest.raises(AuthorizationError, match="Invalid authorization header"):
            decode_authorization(encoded)

    def test_whitespace_only_raises(self):
        encoded = base64.b64encode(b"   ").decode()
        with pytest.raises(AuthorizationError, match="Invalid authorization header"):
            decode_authorization(encoded)


def _create_test_app() -> FastAPI:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/test")
    def test_route(moderator: str = Depends(get_current_moderator)):
        return {"moderator": moderator}

    return app


class TestGetCurrentModerator:
    def test_valid_header(self):
        client = TestClient(_create_test_app())
        encoded = base64.b64encode(b"alice").decode()

        response = client.get("/test", headers={"Authorization": encoded})

        assert response.status_code == 200
        assert response.json() == {"moderator": "alice"}

    def test_missing_header_returns_401(self):
        client = TestClient(_create_test_app(), raise_server_exceptions=False)

        response = client.get("/test")

        assert response.status_code == 401
        assert response.json() == {"error": "Authorization header required"}

    def test_invalid_base64_returns_401(self):
        client = TestClient(_create_test_app(), raise_server_exceptions=False)

        response = client.get("/test", headers={"Authorization": "!!!invalid!!!"})

        assert response.status_code == 401
        assert response.json() == {"error": "Invalid authorization header"}

    def test_empty_base64_returns_401(self):
        client = TestClient(_create_test_app(), raise_server_exceptions=False)
        encoded = base64.b64encode(b"").decode()

        response = client.get("/test", headers={"Authorization": encoded})

        assert response.status_code == 401
        assert response.json() == {"error": "Authorization header required"}
