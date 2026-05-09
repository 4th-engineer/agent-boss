"""SQLite database for session persistence."""
import sqlite3
from pathlib import Path
from typing import Optional
import uuid


DB_PATH = Path(__file__).parent.parent / "agentboss.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database schema."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tab_id TEXT UNIQUE NOT NULL,
                tab_title TEXT NOT NULL,
                working_dir TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_active_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        """)


def create_session(title: str = "PowerShell", working_dir: Optional[str] = None) -> str:
    tab_id = str(uuid.uuid4())
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO sessions (tab_id, tab_title, working_dir) VALUES (?, ?, ?)",
            (tab_id, title, working_dir),
        )
    return tab_id


def update_session(tab_id: str, title: Optional[str] = None, working_dir: Optional[str] = None):
    with get_connection() as conn:
        if title is not None:
            conn.execute(
                "UPDATE sessions SET tab_title = ?, last_active_at = CURRENT_TIMESTAMP WHERE tab_id = ?",
                (title, tab_id),
            )
        if working_dir is not None:
            conn.execute(
                "UPDATE sessions SET working_dir = ?, last_active_at = CURRENT_TIMESTAMP WHERE tab_id = ?",
                (working_dir, tab_id),
            )


def remove_session(tab_id: str):
    with get_connection() as conn:
        conn.execute("DELETE FROM sessions WHERE tab_id = ?", (tab_id,))


def get_all_sessions() -> list:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM sessions ORDER BY last_active_at DESC"
        ).fetchall()


def get_setting(key: str) -> Optional[str]:
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None


def set_setting(key: str, value: str):
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
