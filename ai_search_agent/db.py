import os
import json
import sqlite3
import time
from typing import Any, Dict, List, Optional, Tuple

DB_PATH = os.environ.get("ASA_DB_PATH", os.path.join(os.getcwd(), "asa.db"))


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _get_conn()
    try:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                ts INTEGER NOT NULL,
                question TEXT NOT NULL,
                result TEXT NOT NULL
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS shares (
                share_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                created_at INTEGER NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def save_run(session_id: str, run_id: str, question: str, result: Dict[str, Any]) -> None:
    conn = _get_conn()
    try:
        c = conn.cursor()
        c.execute(
            "INSERT INTO runs (id, session_id, ts, question, result) VALUES (?, ?, ?, ?, ?)",
            (run_id, session_id, int(time.time()), question, json.dumps(result)),
        )
        conn.commit()
    finally:
        conn.close()


def list_runs(session_id: str) -> List[Dict[str, Any]]:
    conn = _get_conn()
    try:
        c = conn.cursor()
        rows = c.execute(
            "SELECT id, ts, question, result FROM runs WHERE session_id = ? ORDER BY ts DESC",
            (session_id,),
        ).fetchall()
        metas: List[Dict[str, Any]] = []
        for r in rows:
            try:
                has_answer = bool(json.loads(r["result"]).get("final_answer"))
            except Exception:
                has_answer = False
            metas.append(
                {
                    "id": r["id"],
                    "ts": r["ts"],
                    "question": r["question"],
                    "has_answer": has_answer,
                }
            )
        return metas
    finally:
        conn.close()


def get_run(session_id: str, run_id: str) -> Optional[Dict[str, Any]]:
    conn = _get_conn()
    try:
        c = conn.cursor()
        row = c.execute(
            "SELECT id, ts, question, result FROM runs WHERE session_id = ? AND id = ?",
            (session_id, run_id),
        ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "ts": row["ts"],
            "question": row["question"],
            "result": json.loads(row["result"]),
        }
    finally:
        conn.close()


def clear_runs(session_id: str) -> None:
    conn = _get_conn()
    try:
        c = conn.cursor()
        c.execute("DELETE FROM runs WHERE session_id = ?", (session_id,))
        conn.commit()
    finally:
        conn.close()


def create_share(run_id: str, share_id: str) -> None:
    conn = _get_conn()
    try:
        c = conn.cursor()
        c.execute(
            "INSERT INTO shares (share_id, run_id, created_at) VALUES (?, ?, ?)",
            (share_id, run_id, int(time.time())),
        )
        conn.commit()
    finally:
        conn.close()


def get_shared(share_id: str) -> Optional[Dict[str, Any]]:
    conn = _get_conn()
    try:
        c = conn.cursor()
        row = c.execute(
            "SELECT r.id, r.ts, r.question, r.result FROM shares s JOIN runs r ON s.run_id = r.id WHERE s.share_id = ?",
            (share_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "ts": row["ts"],
            "question": row["question"],
            "result": json.loads(row["result"]),
        }
    finally:
        conn.close()

