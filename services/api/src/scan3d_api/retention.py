"""Retention. Never removes protected artifacts or any artifact a protected one derives from.

`python -m scan3d_api.retention [--dry-run]` uses SCAN3D_DB and the data dir beside it.
"""

import os
import sqlite3
import sys
from datetime import timedelta
from pathlib import Path

from scan3d_api import auth, db
from scan3d_api.uploads import partial_path

STALE_UPLOAD = timedelta(hours=24)
INTERMEDIATE_TTL = timedelta(days=30)


def purge(
    conn: sqlite3.Connection, data_dir: Path, *, dry_run: bool = False
) -> dict[str, list[str]]:
    """Return ids removed (or that would be removed) by kind, so replay gaps can be reported."""
    now = auth.now()
    stale = [
        r["id"]
        for r in conn.execute(
            "SELECT id FROM uploads WHERE status='open' AND updated_at < ?",
            ((now - STALE_UPLOAD).isoformat(),),
        )
    ]
    # Intermediates only, and only if no protected artifact lists them as its parent.
    old = [
        r["id"]
        for r in conn.execute(
            "SELECT a.id FROM artifacts a WHERE a.protected=0 AND a.created_at < ? AND NOT EXISTS"
            " (SELECT 1 FROM artifacts c WHERE c.parent_id=a.id AND c.protected=1)",
            ((now - INTERMEDIATE_TTL).isoformat(),),
        )
    ]
    if not dry_run:
        for upload_id in stale:
            partial_path(data_dir, upload_id).unlink(missing_ok=True)
            conn.execute("DELETE FROM uploads WHERE id=?", (upload_id,))
        for artifact_id in old:
            path = conn.execute("SELECT path FROM artifacts WHERE id=?", (artifact_id,)).fetchone()
            (data_dir / path["path"]).unlink(missing_ok=True)
            conn.execute("DELETE FROM artifacts WHERE id=?", (artifact_id,))
    return {"stale_uploads": stale, "intermediates": old}


if __name__ == "__main__":
    db_path = Path(os.environ.get("SCAN3D_DB", "data/scan3d.sqlite"))
    c = db.connect(db_path)
    try:
        print(purge(c, db_path.parent / "files", dry_run="--dry-run" in sys.argv))
    finally:
        c.close()
