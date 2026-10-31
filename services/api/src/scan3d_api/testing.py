"""Test harness shared by the API tests."""

from pathlib import Path

from fastapi.testclient import TestClient

from scan3d_api import auth, db
from scan3d_api.app import create_app


class Harness:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.client = TestClient(create_app(path, secure_cookies=False))

    def invite(self, *, admin: bool = False) -> str:
        conn = db.connect(self.path)
        try:
            return auth.create_invite(conn, is_admin=admin)
        finally:
            conn.close()

    def new_user(self, email: str, *, admin: bool = False) -> TestClient:
        """A fresh logged-in client with its own cookie jar and CSRF header."""
        client = TestClient(self.client.app)
        r = client.post(
            "/api/auth/register",
            json={
                "invite": self.invite(admin=admin),
                "email": email,
                "password": "correct horse 1",
            },
        )
        assert r.status_code == 200, r.text
        client.headers["x-csrf-token"] = r.json()["csrf"]
        return client
