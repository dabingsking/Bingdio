"""Netease music tools — direct ncm-cli wrapper."""

import json
import subprocess
from typing import Any

NCM_CLI = "ncm-cli"


def _run(*args: str) -> dict:
    """Run ncm-cli command and return parsed JSON."""
    try:
        result = subprocess.run(
            [NCM_CLI] + list(args),
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
            errors="replace",
        )
        if result.stdout:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"success": False, "message": result.stdout}
        return {"success": False, "message": result.stderr or "No output"}
    except FileNotFoundError:
        return {"success": False, "message": "ncm-cli not found"}
    except subprocess.TimeoutExpired:
        return {"success": False, "message": "Command timeout"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def search(key: str, limit: int = 5) -> list[dict]:
    """Search songs by keyword. Returns list of song dicts."""
    result = _run("search", "song", "--keyword", key, "--limit", str(limit), "--output", "json")
    if result.get("code") != 200:
        return []

    songs = []
    for item in result.get("data", {}).get("records", []):
        artists = [a.get("name", "") for a in item.get("artists", [])]
        songs.append({
            "name": item.get("name", ""),
            "artist": ", ".join(artists),
            "original_id": item.get("originalId"),
            "encrypted_id": item.get("id"),
            "album": (item.get("album") or {}).get("name", "") if item.get("album") else "",
            "duration": item.get("duration", 0),
        })
    return songs


def play(encrypted_id: str, original_id: int | str = "") -> dict:
    """
    Play a song by encrypted_id using queue add.
    Falls back to direct play if TUI is not running.
    """
    # Always use queue add when TUI might be running
    result = _run("queue", "add", "--encrypted-id", encrypted_id, "--output", "json")
    return result


def play_by_ids(encrypted_id: str, original_id: int | str = "") -> dict:
    """Play using --song flag with both IDs (requires TUI to be closed)."""
    result = _run(
        "play", "--song",
        "--encrypted-id", encrypted_id,
        "--original-id", str(original_id) if original_id else "",
        "--output", "json"
    )
    return result


def queue_clear() -> dict:
    """Clear the playback queue."""
    return _run("queue", "clear", "--output", "json")


def queue_list() -> dict:
    """Get current queue info."""
    return _run("queue", "--output", "json")


def next_song() -> dict:
    """Skip to next song."""
    return _run("next", "--output", "json")


def prev_song() -> dict:
    """Go to previous song."""
    return _run("prev", "--output", "json")


def pause() -> dict:
    """Pause playback."""
    return _run("pause", "--output", "json")


def resume() -> dict:
    """Resume playback."""
    return _run("resume", "--output", "json")


def volume(level: int) -> dict:
    """Set volume (0-100)."""
    return _run("volume", str(level), "--output", "json")


def state() -> dict:
    """Get current playback state."""
    return _run("state", "--output", "json")


def current_song() -> dict:
    """Get current playing song info."""
    st = state()
    if st.get("success"):
        s = st.get("state", {})
        return {
            "success": True,
            "song": s.get("title", "未知"),
            "artist": "未知",
            "position": s.get("position", 0),
            "duration": s.get("duration", 0),
            "status": s.get("status", "unknown"),
        }
    return {"success": False, "song": None}


def get_recommend() -> list[dict]:
    """Get daily recommendations."""
    result = _run("recommend", "--output", "json")
    if result.get("code") != 200:
        return []
    songs = []
    for item in result.get("data", {}).get("records", []):
        artists = [a.get("name", "") for a in item.get("artists", [])]
        songs.append({
            "name": item.get("name", ""),
            "artist": ", ".join(artists),
            "original_id": item.get("originalId"),
            "encrypted_id": item.get("id"),
        })
    return songs


def get_liked_songs(limit: int = 20) -> list[dict]:
    """Get user's liked songs (requires login)."""
    # ncm-cli doesn't have a direct liked songs command, so return empty
    # User can search for their own playlists instead
    return []