"""Rule-based intent detection for quick commands (no LLM latency)."""

import re
from typing import Any


# Quick command patterns
_QUICK_PATTERNS = [
    # Playback controls
    (["下一首", "下一曲", "next", "skip", "下一首"], "next", {}),
    (["上一首", "上一曲", "previous", "prev"], "prev", {}),
    (["暂停", "pause", "停止", "stop"], "pause", {}),
    (["继续", "恢复", "resume", "继续播放", "play", "播放"], "resume", {}),
    (["音量加", "音量增加", "大声点", "volume up", "音量+"], "volume_up", {}),
    (["音量减", "音量降低", "小声点", "volume down", "音量-"], "volume_down", {}),
    # Status queries
    (["现在播什么", "当前歌曲", "正在播放什么", "what's playing", "current song", "当前播放"], "current_song", {}),
    (["播放列表", "歌单", "playlist", "队列"], "playlist", {}),
    (["天气", "weather"], "weather", {}),
    # Mood changes
    (["轻松", "轻松的歌", " chill"], "mood", {"mood": "轻松"}),
    (["激烈", "劲爆", "摇滚", "激烈点"], "mood", {"mood": "激烈"}),
    (["安静", "轻音乐", "安静点"], "mood", {"mood": "安静"}),
    (["愉悦", "开心", "快乐", "高兴"], "mood", {"mood": "愉悦"}),
    (["悲伤", "难过", "忧伤了"], "mood", {"mood": "悲伤"}),
    (["浪漫", "柔情", "甜蜜"], "mood", {"mood": "浪漫"}),
]


def detect_intent(user_input: str) -> dict[str, Any] | None:
    """
    Detect user intent using rule-based matching.
    Returns dict with "intent", "tool", "args" or None.
    """
    text = user_input.strip().lower()

    for patterns, intent, args in _QUICK_PATTERNS:
        for p in patterns:
            if p in text:
                return {"intent": intent, "tool": _INTENT_TOOL.get(intent, intent), "args": args}

    # Check for play song intent
    play_patterns = ["播放", "来首歌", "放歌", "唱", "play"]
    for p in play_patterns:
        if p in text:
            # Extract song name after the keyword
            song_name = user_input.strip()
            for kw in play_patterns:
                song_name = song_name.replace(kw, "").strip()
            if song_name:
                return {"intent": "play_song", "tool": "play_song", "args": {"song_name": song_name}}

    return None


def _intent_tool(intent: str) -> str:
    return _INTENT_TOOL.get(intent, intent)


_INTENT_TOOL = {
    "next": "next",
    "prev": "prev",
    "pause": "pause",
    "resume": "resume",
    "volume_up": "volume_up",
    "volume_down": "volume_down",
    "current_song": "current_song",
    "playlist": "playlist",
    "weather": "weather",
    "mood": "change_mood",
    "play_song": "play_song",
}