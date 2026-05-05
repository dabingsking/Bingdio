"""Playlist tool with SQLite storage for mood logs and play history."""

import sqlite3
import os
import yaml
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

E303 = "E303"

ERR_CONFIG_MISSING = f"{E303}01"
ERR_CONFIG_INVALID = f"{E303}02"
ERR_DB_ERROR = f"{E303}03"
ERR_INVALID_PARAM = f"{E303}04"

_CONFIG_CACHE: Optional[Dict[str, Any]] = None


def _load_config() -> Dict[str, Any]:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    config_path = os.environ.get(
        "PLAYLIST_CONFIG_PATH",
        os.path.join(os.path.dirname(__file__), "..", "..", "config.yaml")
    )
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        _CONFIG_CACHE = yaml.safe_load(f)
    return _CONFIG_CACHE


def _get_db_path() -> str:
    config = _load_config()
    db_config = config.get("database", {})
    path = db_config.get("path", "memory/bingdio.db")

    if not os.path.isabs(path):
        base = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(base, path)

    db_dir = os.path.dirname(path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    return path


def _get_conn() -> sqlite3.Connection:
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    _init_tables(conn)
    return conn


def _init_tables(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS mood_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mood_label TEXT NOT NULL,
            mood_score REAL NOT NULL,
            context TEXT,
            song_playing TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS play_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id TEXT NOT NULL,
            song_name TEXT NOT NULL,
            artist TEXT,
            source TEXT,
            played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_mood_created
        ON mood_logs(created_at)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_history_played
        ON play_history(played_at)
    """)

    conn.commit()


def _dt_24h_ago() -> str:
    dt = datetime.now() - timedelta(hours=24)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _error(code: str, msg: str) -> Dict[str, Any]:
    return {"code": code, "msg": msg}


def add_mood_log(mood_label: str, mood_score: float,
                 context: Optional[str] = None,
                 song_playing: Optional[str] = None) -> Dict[str, Any]:
    """Add a mood log entry."""
    try:
        config = _load_config()
    except Exception:
        return _error(ERR_CONFIG_MISSING, "Failed to load config")

    if not isinstance(mood_score, (int, float)):
        return _error(ERR_INVALID_PARAM, "mood_score must be numeric")

    if mood_score < -1 or mood_score > 1:
        return _error(ERR_INVALID_PARAM, "mood_score must be between -1 and 1")

    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO mood_logs (mood_label, mood_score, context, song_playing) VALUES (?, ?, ?, ?)",
            (mood_label, mood_score, context, song_playing)
        )
        conn.commit()
        log_id = cur.lastrowid
        conn.close()
        return {"code": "0", "id": log_id}
    except sqlite3.Error as e:
        return _error(ERR_DB_ERROR, f"Database error: {e}")
    except Exception as e:
        return _error(ERR_DB_ERROR, f"Unexpected error: {e}")


def get_mood_logs(limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    """Get mood log entries, with 24-hour dedup on (mood_label, context, song_playing)."""
    try:
        conn = _get_conn()
        cur = conn.cursor()
        dt_24h = _dt_24h_ago()
        cur.execute("""
            SELECT * FROM (
                SELECT *, ROW_NUMBER() OVER (
                    PARTITION BY mood_label, context, song_playing
                    ORDER BY created_at DESC
                ) as rn
                FROM mood_logs
                WHERE created_at >= ?
            ) sub
            WHERE rn = 1
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (dt_24h, limit, offset))
        rows = cur.fetchall()
        conn.close()
        return {"code": "0", "data": [dict(r) for r in rows]}
    except sqlite3.Error as e:
        return _error(ERR_DB_ERROR, f"Database error: {e}")
    except Exception as e:
        return _error(ERR_DB_ERROR, f"Unexpected error: {e}")


def delete_mood_log(log_id: int) -> Dict[str, Any]:
    """Delete a mood log by ID."""
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM mood_logs WHERE id = ?", (log_id,))
        conn.commit()
        affected = cur.rowcount
        conn.close()
        if affected == 0:
            return _error(ERR_INVALID_PARAM, f"Mood log {log_id} not found")
        return {"code": "0", "deleted": affected}
    except sqlite3.Error as e:
        return _error(ERR_DB_ERROR, f"Database error: {e}")


def add_play_history(song_id: str, song_name: str,
                     artist: Optional[str] = None,
                     source: Optional[str] = None) -> Dict[str, Any]:
    """Add a play history entry."""
    try:
        _load_config()
    except Exception:
        return _error(ERR_CONFIG_MISSING, "Failed to load config")

    if not song_id or not song_name:
        return _error(ERR_INVALID_PARAM, "song_id and song_name are required")

    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO play_history (song_id, song_name, artist, source) VALUES (?, ?, ?, ?)",
            (song_id, song_name, artist, source)
        )
        conn.commit()
        hist_id = cur.lastrowid
        conn.close()
        return {"code": "0", "id": hist_id}
    except sqlite3.Error as e:
        return _error(ERR_DB_ERROR, f"Database error: {e}")


def get_play_history(limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    """Get play history, with 24-hour dedup on (song_id)."""
    try:
        conn = _get_conn()
        cur = conn.cursor()
        dt_24h = _dt_24h_ago()
        cur.execute("""
            SELECT * FROM (
                SELECT *, ROW_NUMBER() OVER (
                    PARTITION BY song_id
                    ORDER BY played_at DESC
                ) as rn
                FROM play_history
                WHERE played_at >= ?
            ) sub
            WHERE rn = 1
            ORDER BY played_at DESC
            LIMIT ? OFFSET ?
        """, (dt_24h, limit, offset))
        rows = cur.fetchall()
        conn.close()
        return {"code": "0", "data": [dict(r) for r in rows]}
    except sqlite3.Error as e:
        return _error(ERR_DB_ERROR, f"Database error: {e}")


def delete_play_history(hist_id: int) -> Dict[str, Any]:
    """Delete a play history entry by ID."""
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM play_history WHERE id = ?", (hist_id,))
        conn.commit()
        affected = cur.rowcount
        conn.close()
        if affected == 0:
            return _error(ERR_INVALID_PARAM, f"Play history {hist_id} not found")
        return {"code": "0", "deleted": affected}
    except sqlite3.Error as e:
        return _error(ERR_DB_ERROR, f"Database error: {e}")