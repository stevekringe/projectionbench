"""SQLite store. Everything needed to reproduce or re-judge a run is kept.

Raw request messages and raw provider responses are stored verbatim. Re-judging
an old run against a new lexicon must never require re-spending on the API, and
anyone disputing a score must be able to read the exact transcript it came from.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id      TEXT PRIMARY KEY,
    started_at  TEXT NOT NULL,
    params      TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS probes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        TEXT NOT NULL REFERENCES runs(run_id),
    subject       TEXT NOT NULL,
    scenario_id   TEXT NOT NULL,
    category      TEXT NOT NULL,
    sample_idx    INTEGER NOT NULL,
    turn_index    INTEGER NOT NULL,
    probe_ordinal INTEGER NOT NULL,   -- 0-based position among this scenario's probes
    user_affect   TEXT NOT NULL,
    expect        TEXT NOT NULL,
    tests         TEXT NOT NULL DEFAULT '',
    system        TEXT,
    messages      TEXT NOT NULL,      -- json: history sent, excluding the response
    response      TEXT NOT NULL,
    raw           TEXT,               -- json: full provider response
    error         TEXT,
    -- paste mode only: did the real reply actually contain the error the next
    -- scripted correction assumes? NULL for API runs, where it is planted.
    planted_realized TEXT
);
CREATE TABLE IF NOT EXISTS judgments (
    probe_id  INTEGER NOT NULL REFERENCES probes(id),
    judge     TEXT NOT NULL,
    verdict   TEXT NOT NULL,          -- json
    error     TEXT,
    PRIMARY KEY (probe_id, judge)
);
CREATE INDEX IF NOT EXISTS idx_probes_run ON probes(run_id);
CREATE INDEX IF NOT EXISTS idx_probes_subject ON probes(subject);
"""


def connect(path: str = "results/fbench.sqlite") -> sqlite3.Connection:
    conn = sqlite3.connect(path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    # Migrate databases created before paste mode existed.
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(probes)")}
    if "planted_realized" not in cols:
        conn.execute("ALTER TABLE probes ADD COLUMN planted_realized TEXT")
        conn.commit()
    return conn


def new_run(conn: sqlite3.Connection, params: dict) -> str:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    conn.execute(
        "INSERT OR REPLACE INTO runs (run_id, started_at, params) VALUES (?, ?, ?)",
        (run_id, datetime.now(timezone.utc).isoformat(), json.dumps(params)),
    )
    conn.commit()
    return run_id


def insert_probe(conn: sqlite3.Connection, row: dict) -> int:
    cols = ", ".join(row)
    marks = ", ".join("?" for _ in row)
    cur = conn.execute(f"INSERT INTO probes ({cols}) VALUES ({marks})", tuple(row.values()))
    return cur.lastrowid


def insert_judgment(
    conn: sqlite3.Connection, probe_id: int, judge: str, verdict: dict, error: str | None = None
) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO judgments (probe_id, judge, verdict, error) VALUES (?, ?, ?, ?)",
        (probe_id, judge, json.dumps(verdict), error),
    )


def probes_for(conn: sqlite3.Connection, run_id: str | None = None) -> list[sqlite3.Row]:
    if run_id:
        return conn.execute("SELECT * FROM probes WHERE run_id = ?", (run_id,)).fetchall()
    return conn.execute("SELECT * FROM probes").fetchall()


def latest_run(conn: sqlite3.Connection) -> str | None:
    r = conn.execute("SELECT run_id FROM runs ORDER BY started_at DESC LIMIT 1").fetchone()
    return r["run_id"] if r else None
