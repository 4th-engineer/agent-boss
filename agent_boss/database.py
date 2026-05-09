"""SQLite database for session persistence."""
import sqlite3
import threading
from pathlib import Path
from typing import Optional
import uuid


DB_PATH = Path(__file__).parent.parent / "agentboss.db"

# Thread-local storage for connections
_thread_local = threading.local()


def get_connection() -> sqlite3.Connection:
    """Get a database connection for the current thread.

    Note: Uses check_same_thread=False for Qt compatibility.
    In production, consider using a connection pool or Qt's
    QSqlDatabase for proper thread safety.
    """
    if not hasattr(_thread_local, 'conn') or _thread_local.conn is None:
        _thread_local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _thread_local.conn.row_factory = sqlite3.Row
    return _thread_local.conn


def init_db():
    """Initialize database schema."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tab_id TEXT UNIQUE NOT NULL,
                tab_title TEXT NOT NULL,
                working_dir TEXT,
                avatar_id TEXT DEFAULT 'beaver',
                room_id TEXT DEFAULT 'main',
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
    if title is None and working_dir is None:
        return
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


def get_session_avatar(tab_id: str) -> Optional[str]:
    """Get avatar for a session."""
    with get_connection() as conn:
        row = conn.execute("SELECT avatar_id FROM sessions WHERE tab_id = ?", (tab_id,)).fetchone()
        return row["avatar_id"] if row else None


def set_session_avatar(tab_id: str, avatar_id: str):
    """Set avatar for a session."""
    with get_connection() as conn:
        conn.execute("UPDATE sessions SET avatar_id = ? WHERE tab_id = ?", (avatar_id, tab_id))


def get_session_room(tab_id: str) -> Optional[str]:
    """Get room for a session."""
    with get_connection() as conn:
        row = conn.execute("SELECT room_id FROM sessions WHERE tab_id = ?", (tab_id,)).fetchone()
        return row["room_id"] if row else None


def set_session_room(tab_id: str, room_id: str):
    """Set room for a session."""
    with get_connection() as conn:
        conn.execute("UPDATE sessions SET room_id = ? WHERE tab_id = ?", (room_id, tab_id))
