"""SQLite database for session persistence."""
import sqlite3
import logging
from pathlib import Path
from typing import Optional
import uuid

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "agentboss.db"

# Module-level singleton connection (check_same_thread=False for Qt signal/slot cross-thread access).
# Retry guard prevents spamming logs during prolonged outages.
_conn: Optional[sqlite3.Connection] = None
_conn_error: bool = False


def get_connection() -> sqlite3.Connection:
    """Get the shared database connection.

    Uses check_same_thread=False so Qt slots running on arbitrary threads can still
    access the connection.  All callers are serialised by Qt's event loop so no
    concurrent access occurs in practice.
    """
    global _conn, _conn_error
    if _conn is None:
        if _conn_error:
            raise sqlite3.Error(
                f"Database unavailable — previous connection attempt at {DB_PATH} failed; "
                "not retrying until a successful connection is established"
            )
        try:
            _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            _conn.row_factory = sqlite3.Row
            _conn_error = False
        except sqlite3.Error as e:
            _conn_error = True
            logger.error("Failed to open database at %s: %s", DB_PATH, e, exc_info=True)
            raise
    return _conn


def init_db():
    """Initialize database schema."""
    try:
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
            # Verify schema after creation
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor}
            if "sessions" not in tables or "settings" not in tables:
                raise RuntimeError("Database schema initialization failed")
        logger.info("Database initialized at %s", DB_PATH)
    except OSError as e:
        # sqlite3.Error is a subclass of OSError, covers path/permission/IO failures
        # RuntimeError covers schema verification failure
        logger.error("Database initialization failed: %s", e, exc_info=True)
        raise
    except RuntimeError as e:
        logger.error("Database schema verification failed: %s", e, exc_info=True)
        raise


def create_session(title: str = "PowerShell", working_dir: Optional[str] = None) -> str:
    tab_id = str(uuid.uuid4())
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO sessions (tab_id, tab_title, working_dir) VALUES (?, ?, ?)",
            (tab_id, title, working_dir),
        )
    return tab_id


def update_session(tab_id: str, title: Optional[str] = None, working_dir: Optional[str] = None) -> None:
    if title is None and working_dir is None:
        return
    with get_connection() as conn:
        # Single UPDATE with NULL handling — 1 DB round-trip instead of 2-3
        conn.execute(
            "UPDATE sessions SET tab_title = COALESCE(?, tab_title), "
            "working_dir = COALESCE(?, working_dir), "
            "last_active_at = CURRENT_TIMESTAMP WHERE tab_id = ?",
            (title, working_dir, tab_id),
        )


def remove_session(tab_id: str):
    with get_connection() as conn:
        conn.execute("DELETE FROM sessions WHERE tab_id = ?", (tab_id,))


def get_all_sessions() -> list[sqlite3.Row]:
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
