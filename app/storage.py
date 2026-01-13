import sqlite3
import json
import time
from typing import Any, Dict, List, Optional, Tuple

DB_PATH = "runs.db"

def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS runs (
      run_id TEXT PRIMARY KEY,
      created_at INTEGER,
      user_goal TEXT,
      status TEXT,
      final_answer TEXT,
      steps_json TEXT,
      proposed_plan_json TEXT,
      context_json TEXT
    )
    """)

    conn.commit()
    conn.close()

def save_run(
    run_id: str,
    user_goal: str,
    status: str,
    final_answer: str,
    steps: List[Dict[str, Any]],
    proposed_plan: Optional[List[Dict[str, Any]]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO runs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            run_id,
            int(time.time()),
            user_goal,
            status,
            final_answer,
            json.dumps(steps),
            json.dumps(proposed_plan) if proposed_plan is not None else None,
            json.dumps(context) if context is not None else None,
        ),
    )
    conn.commit()
    conn.close()

def load_run(run_id: str) -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT run_id, user_goal, status, proposed_plan_json, context_json FROM runs WHERE run_id = ?", (run_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "run_id": row[0],
        "user_goal": row[1],
        "status": row[2],
        "proposed_plan": json.loads(row[3]) if row[3] else None,
        "context": json.loads(row[4]) if row[4] else None,
    }
def list_runs(limit: int = 50) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT run_id, created_at, user_goal, status, final_answer
        FROM runs
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()

    out = []
    for r in rows:
        out.append({
            "run_id": r[0],
            "created_at": r[1],
            "user_goal": r[2],
            "status": r[3],
            "final_answer": r[4],
        })
    return out


def read_run(run_id: str) -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT run_id, created_at, user_goal, status, final_answer, steps_json, proposed_plan_json, context_json
        FROM runs
        WHERE run_id = ?
        """,
        (run_id,),
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "run_id": row[0],
        "created_at": row[1],
        "user_goal": row[2],
        "status": row[3],
        "final_answer": row[4],
        "steps": json.loads(row[5]) if row[5] else [],
        "proposed_plan": json.loads(row[6]) if row[6] else None,
        "context": json.loads(row[7]) if row[7] else None,
    }
