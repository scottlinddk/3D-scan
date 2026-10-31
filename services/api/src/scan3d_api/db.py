"""SQLite (WAL) access. One short-lived connection per request or worker call."""

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
  is_admin INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS invites(
  code_hash TEXT PRIMARY KEY, is_admin INTEGER NOT NULL DEFAULT 0,
  expires_at TEXT NOT NULL, used_by INTEGER REFERENCES users(id));
CREATE TABLE IF NOT EXISTS sessions(
  token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
  csrf TEXT NOT NULL, expires_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS api_tokens(
  id TEXT PRIMARY KEY, token_hash TEXT UNIQUE NOT NULL,
  user_id INTEGER NOT NULL REFERENCES users(id), kind TEXT NOT NULL, label TEXT NOT NULL,
  created_at TEXT NOT NULL, revoked INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS jobs(
  id TEXT PRIMARY KEY, owner_id INTEGER NOT NULL REFERENCES users(id),
  name TEXT NOT NULL, source_kind TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS uploads(
  id TEXT PRIMARY KEY, job_id TEXT NOT NULL REFERENCES jobs(id),
  owner_id INTEGER NOT NULL REFERENCES users(id), kind TEXT NOT NULL, filename TEXT NOT NULL,
  size INTEGER NOT NULL, sha256 TEXT, received INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'open', created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS artifacts(
  id TEXT PRIMARY KEY, job_id TEXT NOT NULL REFERENCES jobs(id),
  owner_id INTEGER NOT NULL REFERENCES users(id), kind TEXT NOT NULL, filename TEXT NOT NULL,
  size INTEGER NOT NULL, sha256 TEXT NOT NULL, path TEXT NOT NULL,
  parent_id TEXT REFERENCES artifacts(id), protected INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL);
"""


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path, timeout=5, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = connect(path)
    try:
        conn.executescript(SCHEMA)
    finally:
        conn.close()
