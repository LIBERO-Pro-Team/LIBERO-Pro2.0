"""SQLite persistence for run and episode scheduling state."""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


class SQLiteRunStore:
    def __init__(self, path: str) -> None:
        if path != ":memory:":
            Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA busy_timeout = 5000")
        self._initialize()

    def create_run(
        self,
        run_id: str,
        owner_id: str,
        status: str,
        created_at: float,
        jobs: List[Dict[str, Any]],
    ) -> None:
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO runs(run_id, owner_id, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (run_id, owner_id, status, created_at, created_at),
            )
            self._connection.executemany(
                """
                INSERT INTO jobs(
                    job_id, run_id, ordinal, status, spec_json, attempt,
                    result_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 0, NULL, ?, ?)
                """,
                [
                    (
                        job["job_id"],
                        run_id,
                        job["ordinal"],
                        job["status"],
                        json.dumps(job["spec"], sort_keys=True, separators=(",", ":")),
                        created_at,
                        created_at,
                    )
                    for job in jobs
                ],
            )

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        row = self._connection.execute(
            "SELECT * FROM runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        return dict(row) if row is not None else None

    def list_jobs(self, run_id: str) -> List[Dict[str, Any]]:
        rows = self._connection.execute(
            "SELECT * FROM jobs WHERE run_id = ? ORDER BY ordinal", (run_id,)
        ).fetchall()
        jobs: List[Dict[str, Any]] = []
        for row in rows:
            job = dict(row)
            job["spec"] = json.loads(job.pop("spec_json"))
            result_json = job.pop("result_json")
            job["result"] = json.loads(result_json) if result_json is not None else None
            jobs.append(job)
        return jobs

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        row = self._connection.execute(
            "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
        ).fetchone()
        if row is None:
            return None
        job = dict(row)
        job["spec"] = json.loads(job.pop("spec_json"))
        result_json = job.pop("result_json")
        job["result"] = json.loads(result_json) if result_json is not None else None
        return job

    def next_queued_job(self, run_id: str) -> Optional[Dict[str, Any]]:
        row = self._connection.execute(
            """
            SELECT job_id FROM jobs
            WHERE run_id = ? AND status = 'queued'
            ORDER BY ordinal LIMIT 1
            """,
            (run_id,),
        ).fetchone()
        return self.get_job(str(row["job_id"])) if row is not None else None

    def find_active_lease(self, run_id: str, runner_id: str) -> Optional[Dict[str, Any]]:
        row = self._connection.execute(
            """
            SELECT leases.* FROM leases
            JOIN jobs ON jobs.job_id = leases.job_id
            WHERE jobs.run_id = ? AND leases.runner_id = ?
              AND leases.status = 'active'
            ORDER BY leases.created_at DESC LIMIT 1
            """,
            (run_id, runner_id),
        ).fetchone()
        return dict(row) if row is not None else None

    def get_lease(self, lease_id: str) -> Optional[Dict[str, Any]]:
        row = self._connection.execute(
            "SELECT * FROM leases WHERE lease_id = ?", (lease_id,)
        ).fetchone()
        return dict(row) if row is not None else None

    def mark_allocating(self, job_id: str, updated_at: float) -> None:
        with self._connection:
            changed = self._connection.execute(
                """
                UPDATE jobs
                SET status = 'allocating', attempt = attempt + 1, updated_at = ?
                WHERE job_id = ? AND status = 'queued'
                """,
                (updated_at, job_id),
            ).rowcount
        if changed != 1:
            raise RuntimeError("Episode job is no longer queued")

    def activate_lease(
        self,
        job_id: str,
        lease_id: str,
        runner_id: str,
        session_id: str,
        expires_at: float,
        initial_payload: bytes,
        updated_at: float,
    ) -> bool:
        with self._connection:
            job = self._connection.execute(
                "SELECT status FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
            if job is None or job["status"] != "allocating":
                return False
            self._connection.execute(
                """
                INSERT INTO leases(
                    lease_id, job_id, runner_id, session_id, status, expires_at,
                    initial_payload, created_at, updated_at
                ) VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?)
                """,
                (
                    lease_id,
                    job_id,
                    runner_id,
                    session_id,
                    expires_at,
                    initial_payload,
                    updated_at,
                    updated_at,
                ),
            )
            self._connection.execute(
                """
                UPDATE jobs
                SET status = 'leased', lease_id = ?, session_id = ?, updated_at = ?
                WHERE job_id = ? AND status = 'allocating'
                """,
                (lease_id, session_id, updated_at, job_id),
            )
            self._connection.execute(
                """
                UPDATE runs SET status = 'running', updated_at = ?
                WHERE run_id = (SELECT run_id FROM jobs WHERE job_id = ?)
                  AND status = 'queued'
                """,
                (updated_at, job_id),
            )
        return True

    def requeue_allocation(self, job_id: str, updated_at: float) -> None:
        with self._connection:
            self._connection.execute(
                """
                UPDATE jobs SET status = 'queued', updated_at = ?
                WHERE job_id = ? AND status = 'allocating'
                """,
                (updated_at, job_id),
            )

    def mark_lease_completing(self, lease_id: str, updated_at: float) -> None:
        with self._connection:
            changed = self._connection.execute(
                """
                UPDATE leases SET status = 'completing', updated_at = ?
                WHERE lease_id = ? AND status = 'active'
                """,
                (updated_at, lease_id),
            ).rowcount
            self._connection.execute(
                """
                UPDATE jobs SET status = 'completing', updated_at = ?
                WHERE lease_id = ? AND status = 'leased'
                """,
                (updated_at, lease_id),
            )
        if changed != 1:
            raise RuntimeError("Lease is no longer active")

    def extend_lease(self, lease_id: str, expires_at: float, updated_at: float) -> None:
        with self._connection:
            changed = self._connection.execute(
                """
                UPDATE leases SET expires_at = ?, updated_at = ?
                WHERE lease_id = ? AND status = 'active'
                """,
                (expires_at, updated_at, lease_id),
            ).rowcount
        if changed != 1:
            raise RuntimeError("Lease is no longer active")

    def restore_active_lease(self, lease_id: str, updated_at: float) -> None:
        with self._connection:
            self._connection.execute(
                """
                UPDATE leases SET status = 'active', updated_at = ?
                WHERE lease_id = ? AND status = 'completing'
                """,
                (updated_at, lease_id),
            )
            self._connection.execute(
                """
                UPDATE jobs SET status = 'leased', updated_at = ?
                WHERE lease_id = ? AND status = 'completing'
                """,
                (updated_at, lease_id),
            )

    def abandon_lease(self, lease_id: str, updated_at: float) -> bool:
        lease = self._connection.execute(
            "SELECT job_id FROM leases WHERE lease_id = ?", (lease_id,)
        ).fetchone()
        if lease is None:
            return False
        job_id = str(lease["job_id"])
        with self._connection:
            changed = self._connection.execute(
                """
                UPDATE leases SET status = 'abandoned', updated_at = ?
                WHERE lease_id = ? AND status = 'active'
                """,
                (updated_at, lease_id),
            ).rowcount
            if changed != 1:
                return False
            self._connection.execute(
                """
                UPDATE jobs
                SET status = 'queued', lease_id = NULL, session_id = NULL, updated_at = ?
                WHERE job_id = ? AND status = 'leased'
                """,
                (updated_at, job_id),
            )
            run = self._connection.execute(
                "SELECT run_id FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
            run_id = str(run["run_id"])
            active = self._connection.execute(
                """
                SELECT COUNT(*) AS count FROM jobs
                WHERE run_id = ? AND status IN ('allocating', 'leased', 'completing')
                """,
                (run_id,),
            ).fetchone()
            status = "running" if int(active["count"]) else "queued"
            self._connection.execute(
                "UPDATE runs SET status = ?, updated_at = ? WHERE run_id = ?",
                (status, updated_at, run_id),
            )
        return True

    def complete_lease(
        self, lease_id: str, result: Dict[str, Any], updated_at: float
    ) -> bool:
        result_json = json.dumps(result, sort_keys=True, separators=(",", ":"))
        with self._connection:
            lease = self._connection.execute(
                "SELECT job_id FROM leases WHERE lease_id = ?", (lease_id,)
            ).fetchone()
            if lease is None:
                raise RuntimeError("Lease disappeared during completion")
            job_id = str(lease["job_id"])
            lease_changed = self._connection.execute(
                """
                UPDATE leases SET status = 'completed', updated_at = ?
                WHERE lease_id = ? AND status = 'completing'
                """,
                (updated_at, lease_id),
            ).rowcount
            job_changed = self._connection.execute(
                """
                UPDATE jobs SET status = 'completed', result_json = ?, updated_at = ?
                WHERE job_id = ? AND status = 'completing'
                """,
                (result_json, updated_at, job_id),
            ).rowcount
            if lease_changed != 1 or job_changed != 1:
                return False
            run_id_row = self._connection.execute(
                "SELECT run_id FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
            run_id = str(run_id_row["run_id"])
            unfinished = self._connection.execute(
                "SELECT COUNT(*) AS count FROM jobs WHERE run_id = ? AND status != 'completed'",
                (run_id,),
            ).fetchone()
            if int(unfinished["count"]) == 0:
                self._connection.execute(
                    "UPDATE runs SET status = 'completed', updated_at = ? WHERE run_id = ?",
                    (updated_at, run_id),
                )
        return True

    def expire_due_leases(self, now: float) -> List[Dict[str, Any]]:
        rows = self._connection.execute(
            """
            SELECT leases.*, jobs.run_id FROM leases
            JOIN jobs ON jobs.job_id = leases.job_id
            WHERE leases.status = 'active' AND leases.expires_at <= ?
            ORDER BY leases.expires_at, leases.lease_id
            """,
            (now,),
        ).fetchall()
        expired: List[Dict[str, Any]] = []
        with self._connection:
            for row in rows:
                lease = dict(row)
                changed = self._connection.execute(
                    """
                    UPDATE leases SET status = 'expired', updated_at = ?
                    WHERE lease_id = ? AND status = 'active'
                    """,
                    (now, lease["lease_id"]),
                ).rowcount
                if changed != 1:
                    continue
                self._connection.execute(
                    """
                    UPDATE jobs
                    SET status = 'queued', lease_id = NULL, session_id = NULL, updated_at = ?
                    WHERE job_id = ? AND status = 'leased'
                    """,
                    (now, lease["job_id"]),
                )
                expired.append(lease)

            for run_id in {str(lease["run_id"]) for lease in expired}:
                active = self._connection.execute(
                    """
                    SELECT COUNT(*) AS count FROM jobs
                    WHERE run_id = ? AND status IN ('allocating', 'leased', 'completing')
                    """,
                    (run_id,),
                ).fetchone()
                status = "running" if int(active["count"]) else "queued"
                self._connection.execute(
                    "UPDATE runs SET status = ?, updated_at = ? WHERE run_id = ?",
                    (status, now, run_id),
                )
        return expired

    def cancel_run(self, run_id: str, updated_at: float) -> List[Dict[str, Any]]:
        rows = self._connection.execute(
            """
            SELECT leases.* FROM leases
            JOIN jobs ON jobs.job_id = leases.job_id
            WHERE jobs.run_id = ? AND leases.status IN ('active', 'completing')
            """,
            (run_id,),
        ).fetchall()
        leases = [dict(row) for row in rows]
        with self._connection:
            self._connection.execute(
                """
                UPDATE leases SET status = 'cancelled', updated_at = ?
                WHERE lease_id IN (
                    SELECT leases.lease_id FROM leases
                    JOIN jobs ON jobs.job_id = leases.job_id
                    WHERE jobs.run_id = ? AND leases.status IN ('active', 'completing')
                )
                """,
                (updated_at, run_id),
            )
            self._connection.execute(
                """
                UPDATE jobs SET status = 'cancelled', updated_at = ?
                WHERE run_id = ?
                  AND status IN ('queued', 'allocating', 'leased', 'completing')
                """,
                (updated_at, run_id),
            )
            self._connection.execute(
                "UPDATE runs SET status = 'cancelled', updated_at = ? WHERE run_id = ?",
                (updated_at, run_id),
            )
        return leases

    def count_pending_jobs(self) -> int:
        row = self._connection.execute(
            """
            SELECT COUNT(*) AS count FROM jobs
            WHERE status IN ('queued', 'allocating', 'leased', 'completing')
            """
        ).fetchone()
        return int(row["count"])

    def count_active_jobs_for_owner(self, owner_id: str) -> int:
        row = self._connection.execute(
            """
            SELECT COUNT(*) AS count FROM jobs
            JOIN runs ON runs.run_id = jobs.run_id
            WHERE runs.owner_id = ?
              AND jobs.status IN ('allocating', 'leased', 'completing')
            """,
            (owner_id,),
        ).fetchone()
        return int(row["count"])

    def count_active_leases(self) -> int:
        row = self._connection.execute(
            "SELECT COUNT(*) AS count FROM leases WHERE status IN ('active', 'completing')"
        ).fetchone()
        return int(row["count"])

    def recover_interrupted(self, updated_at: float) -> int:
        interrupted_row = self._connection.execute(
            """
            SELECT COUNT(*) AS count FROM jobs
            WHERE status IN ('allocating', 'leased', 'completing')
            """
        ).fetchone()
        interrupted = int(interrupted_row["count"])
        if interrupted == 0:
            return 0
        with self._connection:
            self._connection.execute(
                """
                UPDATE leases SET status = 'expired', updated_at = ?
                WHERE status IN ('active', 'completing')
                """,
                (updated_at,),
            )
            self._connection.execute(
                """
                UPDATE jobs
                SET status = 'queued', lease_id = NULL, session_id = NULL, updated_at = ?
                WHERE status IN ('allocating', 'leased', 'completing')
                """,
                (updated_at,),
            )
            self._connection.execute(
                """
                UPDATE runs SET status = 'queued', updated_at = ?
                WHERE status IN ('queued', 'running')
                  AND EXISTS (
                      SELECT 1 FROM jobs
                      WHERE jobs.run_id = runs.run_id AND jobs.status = 'queued'
                  )
                """,
                (updated_at,),
            )
        return interrupted

    def close(self) -> None:
        self._connection.close()

    def _initialize(self) -> None:
        with self._connection:
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL REFERENCES runs(run_id),
                    ordinal INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    spec_json TEXT NOT NULL,
                    attempt INTEGER NOT NULL,
                    result_json TEXT,
                    lease_id TEXT,
                    session_id TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    UNIQUE(run_id, ordinal)
                );

                CREATE INDEX IF NOT EXISTS jobs_run_status_index
                ON jobs(run_id, status, ordinal);

                CREATE TABLE IF NOT EXISTS leases (
                    lease_id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL REFERENCES jobs(job_id),
                    runner_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    expires_at REAL NOT NULL,
                    initial_payload BLOB NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );

                CREATE INDEX IF NOT EXISTS leases_runner_status_index
                ON leases(runner_id, status);
                """
            )
        self._ensure_column("jobs", "lease_id", "TEXT")
        self._ensure_column("jobs", "session_id", "TEXT")

    def _ensure_column(self, table: str, column: str, declaration: str) -> None:
        columns = {
            str(row["name"])
            for row in self._connection.execute(f"PRAGMA table_info({table})").fetchall()
        }
        if column not in columns:
            with self._connection:
                self._connection.execute(
                    f"ALTER TABLE {table} ADD COLUMN {column} {declaration}"
                )
