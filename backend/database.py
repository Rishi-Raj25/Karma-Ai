"""SQLite database for Karma AI — calls, messages, and intel persistence."""

import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "karma.db")

_CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS calls (
    id TEXT PRIMARY KEY,
    caller_number TEXT,
    start_time TEXT NOT NULL,
    end_time TEXT,
    duration_seconds INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    mode TEXT NOT NULL DEFAULT 'twilio',
    threat_level TEXT DEFAULT 'HIGH'
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id TEXT NOT NULL REFERENCES calls(id),
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS intel (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id TEXT NOT NULL REFERENCES calls(id),
    field_name TEXT NOT NULL,
    field_value TEXT NOT NULL,
    confidence REAL DEFAULT 0.5,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create tables if they don't exist."""
    with _get_conn() as conn:
        conn.executescript(_CREATE_TABLES)


# ── Call operations ────────────────────────────────────────────

def create_call(call_id: str, caller: str = "unknown", mode: str = "twilio"):
    now = datetime.now(timezone.utc).isoformat()
    with _get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO calls (id, caller_number, start_time, status, mode) VALUES (?, ?, ?, 'active', ?)",
            (call_id, caller, now, mode),
        )


def end_call(call_id: str, status: str = "completed"):
    now = datetime.now(timezone.utc).isoformat()
    with _get_conn() as conn:
        row = conn.execute("SELECT start_time FROM calls WHERE id = ?", (call_id,)).fetchone()
        duration = 0
        if row and row["start_time"]:
            try:
                start = datetime.fromisoformat(row["start_time"])
                duration = int((datetime.now(timezone.utc) - start).total_seconds())
            except (ValueError, TypeError):
                pass
        conn.execute(
            "UPDATE calls SET end_time = ?, duration_seconds = ?, status = ? WHERE id = ?",
            (now, duration, status, call_id),
        )


def get_active_calls() -> list[dict]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM calls WHERE status = 'active' ORDER BY start_time DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_call(call_id: str) -> dict | None:
    with _get_conn() as conn:
        row = conn.execute("SELECT * FROM calls WHERE id = ?", (call_id,)).fetchone()
        return dict(row) if row else None


def get_call_history(limit: int = 50, offset: int = 0) -> list[dict]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT c.*, "
            "(SELECT COUNT(*) FROM messages WHERE call_id = c.id) AS message_count, "
            "(SELECT COUNT(*) FROM intel WHERE call_id = c.id) AS intel_count "
            "FROM calls c ORDER BY c.start_time DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]


def get_total_calls() -> int:
    with _get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) AS cnt FROM calls").fetchone()
        return row["cnt"] if row else 0


# ── Message operations ─────────────────────────────────────────

def save_message(call_id: str, role: str, content: str):
    now = datetime.now(timezone.utc).isoformat()
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO messages (call_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (call_id, role, content, now),
        )


def get_call_transcript(call_id: str) -> list[dict]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT role, content, timestamp FROM messages WHERE call_id = ? ORDER BY id ASC",
            (call_id,),
        ).fetchall()
        return [dict(r) for r in rows]


# ── Intel operations ───────────────────────────────────────────

def save_intel(call_id: str, field_name: str, field_value: str, confidence: float = 0.5):
    with _get_conn() as conn:
        # Don't insert duplicates for same call + field + value
        existing = conn.execute(
            "SELECT id FROM intel WHERE call_id = ? AND field_name = ? AND field_value = ?",
            (call_id, field_name, field_value),
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO intel (call_id, field_name, field_value, confidence) VALUES (?, ?, ?, ?)",
                (call_id, field_name, field_value, confidence),
            )


def get_call_intel(call_id: str) -> list[dict]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT field_name, field_value, confidence, timestamp FROM intel WHERE call_id = ? ORDER BY id ASC",
            (call_id,),
        ).fetchall()
        return [dict(r) for r in rows]


# ── Stats / Analytics ──────────────────────────────────────────

def get_stats() -> dict:
    with _get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM calls").fetchone()["c"]
        active = conn.execute("SELECT COUNT(*) AS c FROM calls WHERE status = 'active'").fetchone()["c"]
        completed = conn.execute("SELECT COUNT(*) AS c FROM calls WHERE status = 'completed'").fetchone()["c"]

        avg_dur = conn.execute(
            "SELECT AVG(duration_seconds) AS a FROM calls WHERE status = 'completed' AND duration_seconds > 0"
        ).fetchone()["a"] or 0

        total_time = conn.execute(
            "SELECT SUM(duration_seconds) AS s FROM calls WHERE duration_seconds > 0"
        ).fetchone()["s"] or 0

        intel_count = conn.execute("SELECT COUNT(*) AS c FROM intel").fetchone()["c"]

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        calls_today = conn.execute(
            "SELECT COUNT(*) AS c FROM calls WHERE start_time LIKE ?", (f"{today}%",)
        ).fetchone()["c"]

        # Calls per day for last 7 days
        daily = []
        for i in range(6, -1, -1):
            from datetime import timedelta
            day = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
            count = conn.execute(
                "SELECT COUNT(*) AS c FROM calls WHERE start_time LIKE ?", (f"{day}%",)
            ).fetchone()["c"]
            daily.append(count)

        return {
            "total_calls": total,
            "active_calls": active,
            "completed_calls": completed,
            "avg_duration_seconds": round(avg_dur),
            "total_time_wasted_seconds": total_time,
            "intel_extracted": intel_count,
            "success_rate": round((completed / total * 100) if total > 0 else 0, 1),
            "calls_today": calls_today,
            "calls_this_week": daily,
        }
