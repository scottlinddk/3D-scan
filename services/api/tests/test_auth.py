from fastapi.testclient import TestClient
from scan3d_api.testing import Harness


def test_invite_is_single_use_and_required(h: Harness) -> None:
    code = h.invite()
    body = {"invite": code, "email": "a@x.io", "password": "correct horse 1"}
    assert h.client.post("/api/auth/register", json={**body, "invite": "bogus"}).status_code == 403
    assert h.client.post("/api/auth/register", json=body).status_code == 200
    assert h.client.post("/api/auth/register", json={**body, "email": "b@x.io"}).status_code == 403


def test_login_logout_and_bad_credentials(h: Harness) -> None:
    h.new_user("a@x.io")
    c = TestClient(h.client.app)
    bad = {"email": "a@x.io", "password": "wrong password"}
    assert c.post("/api/auth/login", json=bad).status_code == 401
    assert c.post("/api/auth/login", json={"email": "no@x.io", "password": "x"}).status_code == 401
    r = c.post("/api/auth/login", json={"email": "A@x.io", "password": "correct horse 1"})
    assert r.status_code == 200
    c.headers["x-csrf-token"] = r.json()["csrf"]
    assert c.get("/api/auth/me").json()["user_id"] == r.json()["user_id"]
    assert c.post("/api/auth/logout").status_code == 204
    assert c.get("/api/auth/me").status_code == 401


def test_csrf_required_for_cookie_writes(h: Harness) -> None:
    c = h.new_user("a@x.io")
    del c.headers["x-csrf-token"]
    assert c.post("/api/jobs", json={"name": "x"}).status_code == 403
    assert c.get("/api/jobs").status_code == 200


def test_only_admin_creates_invites(h: Harness) -> None:
    assert h.new_user("u@x.io").post("/api/auth/invites", json={}).status_code == 403
    assert h.new_user("adm@x.io", admin=True).post("/api/auth/invites", json={}).status_code == 201


def test_device_and_worker_token_scopes(h: Harness) -> None:
    user = h.new_user("a@x.io")
    dev = user.post("/api/tokens", json={"kind": "device", "label": "phone"}).json()
    wrk = user.post("/api/tokens", json={"kind": "worker", "label": "mac"}).json()

    bare = TestClient(h.client.app)  # no cookies: bearer only
    d = {"authorization": f"Bearer {dev['token']}"}
    w = {"authorization": f"Bearer {wrk['token']}"}
    assert bare.post("/api/jobs", json={"name": "scan"}, headers=d).status_code == 201
    assert (
        bare.post("/api/tokens", json={"kind": "worker", "label": "x"}, headers=d).status_code
        == 403
    )
    assert bare.post("/api/jobs", json={"name": "scan"}, headers=w).status_code == 403
    assert bare.get("/api/jobs", headers={"authorization": "Bearer nope"}).status_code == 401

    assert user.delete(f"/api/tokens/{dev['id']}").status_code == 204
    assert bare.get("/api/jobs", headers=d).status_code == 401
