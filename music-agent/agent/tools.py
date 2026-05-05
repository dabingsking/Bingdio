"""Tool definitions for the Bingody agent."""

from typing import Any, Callable

# Tool definitions for LLM (JSON schema format)
TOOL_DEFINITIONS = [
    {
        "name": "search_song",
        "description": "Search for songs by name or keyword. Returns multiple results.",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "Song name or search keyword"},
                "limit": {"type": "integer", "description": "Maximum results (default 5)", "default": 5},
            },
            "required": ["keyword"],
        },
    },
    {
        "name": "play_song",
        "description": "Play a song. Accepts song name (auto-searches), encrypted ID (32-char hex), or any search keyword.",
        "parameters": {
            "type": "object",
            "properties": {
                "song_id": {"type": "string", "description": "Song ID, encrypted ID, or song name"},
            },
        },
    },
    {
        "name": "get_current_song",
        "description": "Get information about the currently playing song.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "next_song",
        "description": "Skip to the next song in the playlist.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "prev_song",
        "description": "Go to the previous song in the playlist.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "pause",
        "description": "Pause playback.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "resume",
        "description": "Resume playback.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "volume_up",
        "description": "Increase volume by 10.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "volume_down",
        "description": "Decrease volume by 10.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "get_weather",
        "description": "Get current weather information.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "get_lyric",
        "description": "Get lyrics for a song.",
        "parameters": {
            "type": "object",
            "properties": {
                "song_id": {"type": "string", "description": "Song ID or encrypted ID"},
            },
        },
    },
    {
        "name": "add_mood_log",
        "description": "Log the user's current mood.",
        "parameters": {
            "type": "object",
            "properties": {
                "mood_label": {"type": "string", "description": "Mood label: 开心/愉悦/平静/轻松/焦虑/难过/悲伤"},
                "mood_score": {"type": "number", "description": "Mood score from -1.0 (worst) to 1.0 (best)"},
                "context": {"type": "string", "description": "Optional context about the mood"},
            },
            "required": ["mood_label", "mood_score"],
        },
    },
    {
        "name": "speak",
        "description": "Speak text via TTS (Text-to-Speech). Use for important feedback to user.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to speak"},
                "voice": {"type": "string", "description": "Voice name (default: 冰糖)", "default": "冰糖"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "change_mood",
        "description": "Change the playlist mood. Agent will rebuild playlist with songs matching the new mood.",
        "parameters": {
            "type": "object",
            "properties": {
                "mood": {"type": "string", "description": "Mood keyword: 轻松/激烈/安静/愉悦/悲伤/浪漫"},
            },
            "required": ["mood"],
        },
    },
    {
        "name": "get_playlist",
        "description": "Get information about the current playlist.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
]


class ToolRegistry:
    """Registry mapping tool names to Python callables."""

    def __init__(self):
        self._tools: dict[str, Callable] = {}

    def register(self, name: str, func: Callable) -> None:
        """Register a tool function."""
        self._tools[name] = func

    def call(self, name: str, **kwargs) -> Any:
        """Call a registered tool."""
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")
        return self._tools[name](**kwargs)

    def get_tool_names(self) -> list[str]:
        """Get list of registered tool names."""
        return list(self._tools.keys())


def build_tool_registry() -> ToolRegistry:
    """Build and populate the tool registry with all available tools."""
    from tools.weather import get_weather
    from tools.netease import search_song, play_song, get_lyric
    from tools.playlist import add_mood_log, get_mood_logs, get_play_history
    from tools.tts import speak_text

    registry = ToolRegistry()

    # Weather
    registry.register("get_weather", lambda: get_weather())

    # Netease music
    registry.register("search_song", lambda keyword="", limit=5: search_song(keyword, limit))
    registry.register("play_song", lambda song_id=None: play_song(song_id) if song_id else {"code": "E999", "msg": "song_id required"})
    registry.register("get_lyric", lambda song_id=None: get_lyric(song_id) if song_id else {"code": "E999", "msg": "song_id required"})

    # Playback control - these will be implemented via ncm-cli
    registry.register("next_song", _next_song)
    registry.register("prev_song", _prev_song)
    registry.register("pause", _pause)
    registry.register("resume", _resume)
    registry.register("volume_up", _volume_up)
    registry.register("volume_down", _volume_down)
    registry.register("get_current_song", _get_current_song)
    registry.register("get_playlist", _get_playlist)

    # Mood & history
    registry.register("add_mood_log", lambda mood_label="", mood_score=0, context="": add_mood_log(mood_label, mood_score, context))
    registry.register("get_mood_logs", lambda limit=5: get_mood_logs(limit=limit))
    registry.register("get_play_history", lambda limit=10: get_play_history(limit=limit))

    # TTS
    registry.register("speak", lambda text="", voice="冰糖": speak_text(text, voice) if text else {"code": "E999", "msg": "text required"})

    return registry


def _ncm_cli(*args: str) -> dict:
    """Execute ncm-cli command and return JSON result."""
    import json
    import subprocess

    NCM_CLI = "C:\\Users\\Administrator\\AppData\\Roaming\\npm\\ncm-cli.cmd"
    cmd = [NCM_CLI] + list(args)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15,
            encoding="utf-8",
            errors="replace",
        )
        if result.stdout:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"success": False, "message": result.stdout}
        return {"success": False, "message": result.stderr or "No output"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def _next_song() -> dict:
    """Skip to next song."""
    return _ncm_cli("next")


def _prev_song() -> dict:
    """Go to previous song."""
    return _ncm_cli("prev")


def _pause() -> dict:
    """Pause playback."""
    return _ncm_cli("pause")


def _resume() -> dict:
    """Resume playback."""
    return _ncm_cli("resume")


def _volume_up() -> dict:
    """Increase volume."""
    result = _ncm_cli("state")
    current = result.get("state", {}).get("volume", 50)
    new_vol = min(100, current + 10)
    return _ncm_cli("volume", str(new_vol))


def _volume_down() -> dict:
    """Decrease volume."""
    result = _ncm_cli("state")
    current = result.get("state", {}).get("volume", 50)
    new_vol = max(0, current - 10)
    return _ncm_cli("volume", str(new_vol))


def _get_current_song() -> dict:
    """Get currently playing song info."""
    result = _ncm_cli("state")
    if result.get("success"):
        state = result.get("state", {})
        return {
            "success": True,
            "song": state.get("title", "未知"),
            "artist": state.get("artist", "未知"),
            "position": state.get("position", 0),
            "duration": state.get("duration", 0),
            "status": state.get("status", "unknown"),
        }
    return {"success": False, "song": None}


def _get_playlist() -> dict:
    """Get current playlist info."""
    # ncm-cli doesn't have a direct playlist query, so return current state
    return _get_current_song()
