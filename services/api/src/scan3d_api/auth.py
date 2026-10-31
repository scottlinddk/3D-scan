"""Invite-only accounts, cookie sessions with CSRF, and scoped device/worker tokens."""

import hashlib
import hmac
import secrets
import sqlite3
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi import Depends, HTTPException, Request

SESSION_COOKIE = "session"
SESSION_TTL = timedelta(days=14)
INVITE_TTL = timedelta(days=7)

type Kind = Literal["user", "device", "worker"]

# Token kinds get fixed scopes. Workers can only claim and complete work.
SCOPES: dict[str, frozenset[str]] = {
    "user": frozenset({"jobs:read", "jobs:write", "uploads:write", "tokens:manage"}),
    "device": frozenset({"jobs:read", "jobs:write", "uploads:write"}),
    "worker": frozenset({"worker:claim"}),
}


@dataclass(frozen=True)
class Principal:
    user_id: int
    kind: Kind
    is_admin: bool
    scopes: frozenset[str]


def now() -> datetime:
    return datetime.now(UTC)


def digest(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    key = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"{salt.hex()}${key.hex()}"


def verify_password(password: str, stored: str) -> bool:
    salt_hex, key_hex = stored.split("$")
    key = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1)
    return hmac.compare_digest(key.hex(), key_hex)


def create_invite(conn: sqlite3.Connection, *, is_admin: bool = False) -> str:
    code = secrets.token_urlsafe(24)
    expires = (now() + INVITE_TTL).isoformat()
    conn.execute(
        "INSERT INTO invites(code_hash, is_admin, expires_at) VALUES (?,?,?)",
        (digest(code), int(is_admin), expires),
    )
    return code


def register(conn: sqlite3.Connection, code: str, email: str, password: str) -> int:
    """Consume an invite and create the user atomically."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        invite = conn.execute(
            "SELECT is_admin, expires_at FROM invites WHERE code_hash=? AND used_by IS NULL",
            (digest(code),),
        ).fetchone()
        if invite is None or datetime.fromisoformat(invite["expires_at"]) < now():
            raise HTTPException(403, "invalid or expired invite")
        try:
            cur = conn.execute(
                "INSERT INTO users(email, password_hash, is_admin, created_at) VALUES (?,?,?,?)",
                (email.lower(), hash_password(password), invite["is_admin"], now().isoformat()),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(409, "email already registered") from None
        user_id = cur.lastrowid
        assert user_id is not None
        conn.execute("UPDATE invites SET used_by=? WHERE code_hash=?", (user_id, digest(code)))
        conn.execute("COMMIT")
        return user_id
    except BaseException:
        conn.execute("ROLLBACK")
        raise


def start_session(conn: sqlite3.Connection, user_id: int) -> tuple[str, str]:
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    conn.execute(
        "INSERT INTO sessions(token_hash, user_id, csrf, expires_at) VALUES (?,?,?,?)",
        (digest(token), user_id, csrf, (now() + SESSION_TTL).isoformat()),
    )
    return token, csrf


def create_token(conn: sqlite3.Connection, user_id: int, kind: Kind, label: str) -> tuple[str, str]:
    token_id, token = secrets.token_hex(8), secrets.token_urlsafe(32)
    conn.execute(
        "INSERT INTO api_tokens(id, token_hash, user_id, kind, label, created_at)"
        " VALUES (?,?,?,?,?,?)",
        (token_id, digest(token), user_id, kind, label, now().isoformat()),
    )
    return token_id, token


def get_db(request: Request) -> Iterator[sqlite3.Connection]:
    from scan3d_api.db import connect

    conn = connect(request.app.state.db_path)
    try:
        yield conn
    finally:
        conn.close()


UNSAFE = {"POST", "PUT", "PATCH", "DELETE"}


def principal(request: Request, conn: sqlite3.Connection = Depends(get_db)) -> Principal:
    bearer = request.headers.get("authorization", "")
    if bearer.lower().startswith("bearer "):
        row = conn.execute(
            "SELECT t.kind, u.id, u.is_admin FROM api_tokens t JOIN users u ON u.id=t.user_id"
            " WHERE t.token_hash=? AND t.revoked=0",
            (digest(bearer[7:].strip()),),
        ).fetchone()
        if row:
            return Principal(row["id"], row["kind"], bool(row["is_admin"]), SCOPES[row["kind"]])
    cookie = request.cookies.get(SESSION_COOKIE)
    if cookie and not bearer:
        row = conn.execute(
            "SELECT s.csrf, s.expires_at, u.id, u.is_admin FROM sessions s"
            " JOIN users u ON u.id=s.user_id WHERE s.token_hash=?",
            (digest(cookie),),
        ).fetchone()
        if row and datetime.fromisoformat(row["expires_at"]) > now():
            if request.method in UNSAFE and not hmac.compare_digest(
                request.headers.get("x-csrf-token", ""), row["csrf"]
            ):
                raise HTTPException(403, "missing or invalid CSRF token")
            return Principal(row["id"], "user", bool(row["is_admin"]), SCOPES["user"])
    raise HTTPException(401, "authentication required")


def require(scope: str) -> Callable[[Principal], Principal]:
    def dep(p: Principal = Depends(principal)) -> Principal:
        if scope not in p.scopes:
            raise HTTPException(403, f"scope {scope} required")
        return p

    return dep


def require_admin(p: Principal = Depends(principal)) -> Principal:
    if not (p.is_admin and p.kind == "user"):
        raise HTTPException(403, "admin required")
    return p
