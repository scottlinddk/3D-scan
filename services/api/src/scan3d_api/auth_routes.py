import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from scan3d_api import auth
from scan3d_api.schemas import (
    InviteCreate,
    InviteOut,
    Login,
    Me,
    Register,
    TokenCreate,
    TokenOut,
)

router = APIRouter(prefix="/api")
Db = Depends(auth.get_db)

# Verified against a dummy hash when the email is unknown, so timing does not reveal accounts.
_DUMMY = auth.hash_password("dummy-password")


def _login_response(request: Request, response: Response, conn: sqlite3.Connection, uid: int) -> Me:
    token, csrf = auth.start_session(conn, uid)
    response.set_cookie(
        auth.SESSION_COOKIE,
        token,
        httponly=True,
        samesite="strict",
        secure=request.app.state.secure_cookies,
        max_age=int(auth.SESSION_TTL.total_seconds()),
    )
    admin = conn.execute("SELECT is_admin FROM users WHERE id=?", (uid,)).fetchone()["is_admin"]
    return Me(user_id=uid, is_admin=bool(admin), csrf=csrf)


@router.post("/auth/register", operation_id="register")
def register(
    body: Register, request: Request, response: Response, conn: sqlite3.Connection = Db
) -> Me:
    uid = auth.register(conn, body.invite, body.email, body.password)
    return _login_response(request, response, conn, uid)


@router.post("/auth/login", operation_id="login")
def login(body: Login, request: Request, response: Response, conn: sqlite3.Connection = Db) -> Me:
    row = conn.execute(
        "SELECT id, password_hash FROM users WHERE email=?", (body.email.lower(),)
    ).fetchone()
    ok = auth.verify_password(body.password, row["password_hash"] if row else _DUMMY)
    if not row or not ok:
        raise HTTPException(401, "invalid credentials")
    return _login_response(request, response, conn, row["id"])


@router.post("/auth/logout", status_code=204, operation_id="logout")
def logout(
    request: Request,
    response: Response,
    _: auth.Principal = Depends(auth.principal),
    conn: sqlite3.Connection = Db,
) -> None:
    cookie = request.cookies.get(auth.SESSION_COOKIE)
    if cookie:
        conn.execute("DELETE FROM sessions WHERE token_hash=?", (auth.digest(cookie),))
    response.delete_cookie(auth.SESSION_COOKIE)


@router.get("/auth/me", operation_id="getMe")
def me(p: auth.Principal = Depends(auth.principal)) -> Me:
    return Me(user_id=p.user_id, is_admin=p.is_admin)


@router.post("/auth/invites", status_code=201, operation_id="createInvite")
def create_invite(
    body: InviteCreate,
    _: auth.Principal = Depends(auth.require_admin),
    conn: sqlite3.Connection = Db,
) -> InviteOut:
    return InviteOut(code=auth.create_invite(conn, is_admin=body.is_admin))


@router.post("/tokens", status_code=201, operation_id="createToken")
def create_token(
    body: TokenCreate,
    p: auth.Principal = Depends(auth.require("tokens:manage")),
    conn: sqlite3.Connection = Db,
) -> TokenOut:
    token_id, token = auth.create_token(conn, p.user_id, body.kind, body.label)
    return TokenOut(id=token_id, token=token)


@router.delete("/tokens/{token_id}", status_code=204, operation_id="revokeToken")
def revoke_token(
    token_id: str,
    p: auth.Principal = Depends(auth.require("tokens:manage")),
    conn: sqlite3.Connection = Db,
) -> None:
    cur = conn.execute(
        "UPDATE api_tokens SET revoked=1 WHERE id=? AND user_id=?", (token_id, p.user_id)
    )
    if cur.rowcount == 0:
        raise HTTPException(404, "token not found")
