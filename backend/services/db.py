"""Analysis runs DB; init and backfill on import."""
import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path

from config import BASE_DIR, DB_PATH

logger = logging.getLogger(__name__)


def db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def db_init() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with db_connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_runs (
              analysis_id TEXT PRIMARY KEY,
              repo TEXT NOT NULL,
              created_at TEXT NOT NULL,
              status TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_analysis_runs_repo_created_at ON analysis_runs(repo, created_at)")
        conn.commit()
    with db_connect() as conn:
        cur = conn.execute("PRAGMA table_info(analysis_runs)")
        columns = [row[1] for row in cur.fetchall()]
        if "initiated_by" not in columns:
            conn.execute("ALTER TABLE analysis_runs ADD COLUMN initiated_by TEXT")
            conn.commit()


def db_insert_run(
    *,
    analysis_id: str,
    repo: str,
    created_at: datetime,
    status: str,
    initiated_by: str | None = None,
) -> None:
    with db_connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO analysis_runs(analysis_id, repo, created_at, status, initiated_by) VALUES(?, ?, ?, ?, ?)",
            (analysis_id, repo, created_at.isoformat(), status, initiated_by),
        )
        conn.commit()


def db_update_run_status(analysis_id: str, status: str) -> None:
    with db_connect() as conn:
        conn.execute("UPDATE analysis_runs SET status = ? WHERE analysis_id = ?", (status, analysis_id))
        conn.commit()


def db_list_runs(repo: str | None = None) -> list[dict]:
    with db_connect() as conn:
        if repo:
            rows = conn.execute(
                "SELECT analysis_id, repo, created_at, status, initiated_by FROM analysis_runs WHERE repo = ? ORDER BY created_at DESC",
                (repo,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT analysis_id, repo, created_at, status, initiated_by FROM analysis_runs ORDER BY created_at DESC"
            ).fetchall()
    out: list[dict] = []
    for r in rows:
        out.append({
            "analysis_id": r["analysis_id"],
            "repo": r["repo"],
            "created_at": r["created_at"],
            "status": r["status"],
            "initiated_by": r["initiated_by"] if r["initiated_by"] is not None else None,
        })
    return out


def db_delete_runs(analysis_ids: set[str]) -> None:
    if not analysis_ids:
        return
    with db_connect() as conn:
        conn.executemany("DELETE FROM analysis_runs WHERE analysis_id = ?", [(aid,) for aid in analysis_ids])
        conn.commit()


def db_existing_ids() -> set[str]:
    with db_connect() as conn:
        rows = conn.execute("SELECT analysis_id FROM analysis_runs").fetchall()
    return {str(r["analysis_id"]) for r in rows}


def parse_repo_from_repo_summary(text: str) -> str | None:
    if not text:
        return None
    first = text.splitlines()[0].strip() if text.splitlines() else ""
    prefix = "# Repository Summary:"
    if first.startswith(prefix):
        val = first[len(prefix):].strip()
        return val or None
    return None


def backfill_db_from_existing_artifacts() -> None:
    """Discover analysis dirs (local + S3) and insert missing runs."""
    from services import s3 as s3_mod
    try:
        existing_ids = db_existing_ids()
    except Exception as e:
        logger.warning("history backfill: failed reading existing ids: %s", str(e))
        existing_ids = set()

    discovered_ids: set[str] = set()
    s3_earliest: dict[str, datetime] = {}

    try:
        if BASE_DIR.exists():
            for d in BASE_DIR.iterdir():
                if d.is_dir() and d.name.startswith("analysis-"):
                    discovered_ids.add(d.name)
    except Exception as e:
        logger.warning("history backfill: local scan failed: %s", str(e))

    if s3_mod.s3_enabled():
        try:
            s3 = s3_mod.get_s3_client()
            bucket = s3_mod.get_s3_bucket()
            prefix = "analysis/"
            token = None
            while True:
                kwargs = {"Bucket": bucket, "Prefix": prefix, "MaxKeys": 1000}
                if token:
                    kwargs["ContinuationToken"] = token
                resp = s3.list_objects_v2(**kwargs)
                for obj in resp.get("Contents", []) or []:
                    key = obj.get("Key", "") or ""
                    if not key.startswith(prefix):
                        continue
                    parts = key.split("/")
                    if len(parts) < 2 or not parts[1]:
                        continue
                    aid = parts[1]
                    discovered_ids.add(aid)
                    lm = obj.get("LastModified")
                    if lm:
                        try:
                            lm_dt = lm if isinstance(lm, datetime) else datetime.fromisoformat(str(lm))
                        except Exception:
                            lm_dt = None
                        if lm_dt:
                            prev = s3_earliest.get(aid)
                            if prev is None or lm_dt < prev:
                                s3_earliest[aid] = lm_dt
                if resp.get("IsTruncated"):
                    token = resp.get("NextContinuationToken")
                    continue
                break
        except Exception as e:
            logger.warning("history backfill: s3 scan failed: %s", str(e))

    to_insert = sorted(discovered_ids - existing_ids)
    if not to_insert:
        return

    inserted = 0
    for aid in to_insert:
        repo = "unknown"
        created_at = datetime.now(timezone.utc)
        status = "completed"
        local_dir = BASE_DIR / aid
        if local_dir.exists() and local_dir.is_dir():
            try:
                created_at = datetime.fromtimestamp(local_dir.stat().st_mtime, tz=timezone.utc)
            except Exception:
                pass
            try:
                rs = local_dir / "repo_summary.md"
                if rs.exists():
                    parsed = parse_repo_from_repo_summary(rs.read_text(encoding="utf-8", errors="replace"))
                    if parsed:
                        repo = parsed
            except Exception:
                pass
        elif aid in s3_earliest:
            created_at = s3_earliest[aid].astimezone(timezone.utc) if s3_earliest[aid].tzinfo else s3_earliest[aid].replace(tzinfo=timezone.utc)

        if repo == "unknown" and s3_mod.s3_enabled():
            try:
                text = s3_mod.s3_get_text(aid, "repo_summary.md")
                parsed = parse_repo_from_repo_summary(text)
                if parsed:
                    repo = parsed
            except Exception:
                pass

        try:
            db_insert_run(analysis_id=aid, repo=repo, created_at=created_at, status=status, initiated_by=None)
            inserted += 1
        except Exception as e:
            logger.warning("history backfill: insert failed analysis_id=%s err=%s", aid, str(e))

    logger.info("history backfill: inserted=%s", inserted)


try:
    db_init()
    backfill_db_from_existing_artifacts()
except Exception as e:
    logger.warning("history init/backfill failed: %s", str(e))
