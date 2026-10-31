"""Bootstrap CLI: `python -m scan3d_api.admin invite [--admin]` prints a one-time invite code."""

import os
import sys
from pathlib import Path

from scan3d_api import auth, db


def main(argv: list[str]) -> int:
    if not argv or argv[0] != "invite":
        print("usage: python -m scan3d_api.admin invite [--admin]", file=sys.stderr)
        return 2
    path = Path(os.environ.get("SCAN3D_DB", "data/scan3d.sqlite"))
    db.init(path)
    conn = db.connect(path)
    try:
        print(auth.create_invite(conn, is_admin="--admin" in argv))
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
