"""
memory.py — User conversation memory
Stores full chat history per user_id in a local SQLite database.
Each user from the integrated app sends their user_id with requests.
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

DB_PATH = Path("data/memory.db")

def _conn():
    DB_PATH.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   TEXT NOT NULL,
            role      TEXT NOT NULL,
            content   TEXT NOT NULL,
            language  TEXT DEFAULT 'en',
            timestamp TEXT NOT NULL
        )
    """)
    con.commit()
    return con

def add_message(user_id: str, role: str, content: str, language: str = "en"):
    """Save a message (role = 'user' or 'assistant') for a user."""
    with _conn() as con:
        con.execute(
            "INSERT INTO history (user_id, role, content, language, timestamp) VALUES (?,?,?,?,?)",
            (user_id, role, content, language, datetime.utcnow().isoformat())
        )

def get_history(user_id: str) -> list[dict]:
    """Get full conversation history for a user as list of {role, content}."""
    with _conn() as con:
        rows = con.execute(
            "SELECT role, content FROM history WHERE user_id=? ORDER BY id ASC",
            (user_id,)
        ).fetchall()
    return [{"role": r[0], "content": r[1]} for r in rows]

def clear_history(user_id: str):
    """Delete all history for a user."""
    with _conn() as con:
        con.execute("DELETE FROM history WHERE user_id=?", (user_id,))

def get_all_users() -> list[str]:
    """List all user IDs that have history."""
    with _conn() as con:
        rows = con.execute("SELECT DISTINCT user_id FROM history").fetchall()
    return [r[0] for r in rows]
