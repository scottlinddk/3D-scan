"""Reconcile the artifact directory with SQLite after a crash.

A crash can leave a published file without a row (orphan), or a row whose file is missing.
Orphans are deleted. Missing files are reported, and the tasks that produced them fail so the
job cannot advance on evidence that no longer exists. Artifacts of tasks that never succeeded are
dropped, because a result is only valid once its task completes.
"""

import sqlite3
from pathlib import Path

from scan3d_api import auth


def reconcile(
    conn: sqlite3.Connection, data_dir: Path, *, dry_run: bool = False
) -> dict[str, list[str]]:
    known = {r["path"] for r in conn.execute("SELECT path FROM artifacts")}
    root = data_dir / "artifacts"
    orphans = (
        [
            str(f.relative_to(data_dir))
            for f in sorted(root.rglob("*"))
            if f.is_file() and str(f.relative_to(data_dir)) not in known
        ]
        if root.exists()
        else []
    )
    missing = [
        r["id"]
        for r in conn.execute("SELECT id, path FROM artifacts")
        if not (data_dir / r["path"]).exists()
    ]
    unfinished = [
        r["id"]
        for r in conn.execute(
            "SELECT a.id FROM artifacts a JOIN tasks t ON t.id=a.task_id"
            " WHERE a.protected=0 AND t.state IN ('failed','cancelled')"
        )
    ]
    if not dry_run:
        for rel in orphans:
            (data_dir / rel).unlink(missing_ok=True)
        for artifact_id in unfinished:
            path = conn.execute("SELECT path FROM artifacts WHERE id=?", (artifact_id,)).fetchone()
            (data_dir / path["path"]).unlink(missing_ok=True)
            conn.execute("DELETE FROM artifacts WHERE id=?", (artifact_id,))
        for artifact_id in missing:
            conn.execute(
                "UPDATE tasks SET state='failed', error='output artifact missing', updated_at=?"
                " WHERE id=(SELECT task_id FROM artifacts WHERE id=?) AND state='succeeded'",
                (auth.now().isoformat(), artifact_id),
            )
    return {"orphan_files": orphans, "missing_artifacts": missing, "dropped_artifacts": unfinished}
