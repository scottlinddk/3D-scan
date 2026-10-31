"""Reconcile the artifact directory with SQLite after a crash.

A crash can leave a published file without a row (orphan), or a row whose file is missing.
Orphans are deleted. Missing files are reported, and the tasks that produced them fail so the
job cannot advance on evidence that no longer exists. Artifacts of tasks that never succeeded are
dropped, because a result is only valid once its task completes.
"""

import sqlite3
from pathlib import Path

from scan3d_api import auth


def _deletable(conn: sqlite3.Connection, candidates: set[str]) -> set[str]:
    """Candidates whose children are all themselves deletable (fixed point, leaves first)."""
    children: dict[str, set[str]] = {}
    for r in conn.execute("SELECT id, parent_id FROM artifacts WHERE parent_id IS NOT NULL"):
        children.setdefault(r["parent_id"], set()).add(r["id"])
    ok = set(candidates)
    changed = True
    while changed:
        changed = False
        for a in list(ok):
            if not children.get(a, set()) <= ok:
                ok.discard(a)
                changed = True
    return ok


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
    # Never drop an artifact that a surviving artifact names as its parent.
    drop = _deletable(conn, set(unfinished))
    kept = [a for a in unfinished if a not in drop]
    if not dry_run:
        for rel in orphans:
            (data_dir / rel).unlink(missing_ok=True)
        conn.execute("BEGIN IMMEDIATE")
        paths = []
        for artifact_id in sorted(drop):
            row = conn.execute("SELECT path FROM artifacts WHERE id=?", (artifact_id,)).fetchone()
            paths.append(row["path"])
        for artifact_id in drop:
            conn.execute("DELETE FROM artifacts WHERE id=?", (artifact_id,))
        conn.execute("COMMIT")
        for rel in paths:  # row first, then file: a crash leaves an orphan, never a dangling row
            (data_dir / rel).unlink(missing_ok=True)
        for artifact_id in missing:
            conn.execute(
                "UPDATE tasks SET state='failed', error='output artifact missing', updated_at=?"
                " WHERE id=(SELECT task_id FROM artifacts WHERE id=?) AND state='succeeded'",
                (auth.now().isoformat(), artifact_id),
            )
    return {
        "orphan_files": orphans,
        "missing_artifacts": missing,
        "dropped_artifacts": sorted(drop),
        "kept_referenced": kept,
    }
