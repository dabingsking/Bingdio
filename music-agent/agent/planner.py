"""Playlist planner — builds playlist from context via LLM."""

import json
import logging
import os
import time
from datetime import datetime
from typing import Any

import requests

logger = logging.getLogger(__name__)


def _find_config() -> dict | None:
    """Find config.yaml from project root or current directory."""
    import yaml
    from pathlib import Path
    candidates = [
        Path.cwd() / "config.yaml",
        Path(__file__).parent.parent / "config.yaml",
    ]
    for cfg_path in candidates:
        if cfg_path.exists():
            with open(cfg_path, encoding="utf-8") as f:
                return yaml.safe_load(f)
    return None


LLM_API_KEY = os.getenv("LLM_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
LLM_BASE_URL = "https://token-plan-cn.xiaomimimo.com/v1"
LLM_MODEL = "xiaomi/mimo-v2.5-pro"
_config_loaded = False


def _ensure_config():
    """Lazily load config and set module-level vars."""
    global LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, _config_loaded
    if _config_loaded:
        return
    _config_loaded = True

    cfg = _find_config()
    if cfg:
        LLM_API_KEY = cfg.get("llm", {}).get("api_key", "") or LLM_API_KEY
        LLM_BASE_URL = cfg.get("llm", {}).get("base_url", LLM_BASE_URL)
        LLM_MODEL = cfg.get("llm", {}).get("model", LLM_MODEL)


def _call_llm(messages: list[dict], temperature: float = 0.8) -> str:
    _ensure_config()
    api_key = LLM_API_KEY or os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("E401: LLM API key not configured")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    resp = requests.post(
        f"{LLM_BASE_URL}/chat/completions",
        headers=headers,
        json=payload,
        timeout=30,
    )
    resp.encoding = "utf-8"
    if resp.status_code != 200:
        try:
            error_detail = resp.json().get("error", {}).get("message", resp.text)
        except Exception:
            error_detail = resp.text
        raise ValueError(f"E101: LLM request failed status={resp.status_code}, detail={error_detail}")

    resp.encoding = "utf-8"
    try:
        data = resp.json()
    except Exception as e:
        raise ValueError(f"E102: LLM response JSON parse failed: {e}")

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise ValueError(f"E103: LLM response structure invalid: {e}")


class PlaylistPlanner:
    """Builds a playlist based on context (weather, mood, history, time)."""

    def build_playlist(
        self,
        weather: dict | None = None,
        mood_logs: list[dict] | None = None,
        play_history: list[dict] | None = None,
        time_of_day: str = "晚上",
        count: int = 5,
    ) -> list[dict]:
        """
        Build a playlist from context via LLM.

        Returns:
            List of dicts with "name", "artist", "reason"
        """
        # Format context for prompt
        context_parts = [f"时间段：{time_of_day}"]

        if weather and weather.get("code") == "0":
            context_parts.append(
                f"天气：{weather.get('text', '')}，{weather.get('temp', '')}°C"
            )

        if mood_logs:
            moods = [m.get("mood_label", "") for m in mood_logs[:3] if m.get("mood_label")]
            if moods:
                context_parts.append(f"用户心情：{', '.join(moods)}")

        if play_history:
            recent = [s.get("song_name", "") for s in play_history[:3] if s.get("song_name")]
            if recent:
                context_parts.append(f"最近播放：{', '.join(recent)}")

        context_str = "\n".join(f"- {p}" for p in context_parts)

        prompt = (
            f"根据以下上下文信息，推荐{count}首最适合当前场景的歌曲。\n"
            f"{context_str}\n\n"
            f"返回 JSON 数组，格式：\n"
            f'[{{"name": "歌曲名", "artist": "歌手", "reason": "推荐理由"}}]\n\n'
            f"只返回 JSON 数组，不要其他内容。歌曲要多样化，不要全部是同一风格。"
        )

        messages = [
            {"role": "system", "content": "你是一个专业的音乐推荐助手，根据用户当前场景推荐最合适的歌曲。只返回 JSON。"},
            {"role": "user", "content": prompt},
        ]

        try:
            result = _call_llm(messages)
            start = result.find("[")
            end = result.rfind("]") + 1
            if start >= 0 and end > start:
                songs = json.loads(result[start:end])
                if isinstance(songs, list) and len(songs) > 0:
                    return songs[:count]
        except Exception as e:
            logger.warning("Playlist planning LLM failed: %s", e)

        # Fallback
        return [
            {"name": "天空之城", "artist": "久石让", "reason": "轻音乐推荐"},
            {"name": "夜曲", "artist": "周杰伦", "reason": "经典歌曲"},
            {"name": "Merry Christmas Mr. Lawrence", "artist": "久石让", "reason": "舒缓旋律"},
            {"name": "起风了", "artist": "买辣椒也用券", "reason": "热门歌曲"},
            {"name": "稻香", "artist": "周杰伦", "reason": "轻松愉悦"},
        ]

    def change_mood_playlist(
        self,
        mood: str,
        weather: dict | None = None,
        time_of_day: str = "晚上",
        count: int = 5,
    ) -> list[dict]:
        """Build a playlist for a specific mood."""
        mood_descriptions = {
            "轻松": "轻松愉悦、节奏明快",
            "激烈": "劲爆摇滚、节奏强烈",
            "安静": "安静舒缓、轻柔旋律",
            "愉悦": "开心快乐、欢快轻松",
            "悲伤": "深情忧郁、慢节奏",
            "浪漫": "浪漫柔情、甜蜜温馨",
        }
        desc = mood_descriptions.get(mood, mood)

        context_parts = [
            f"时间段：{time_of_day}",
            f"期望心情：{desc}",
        ]
        if weather and weather.get("code") == "0":
            context_parts.append(f"天气：{weather.get('text', '')}，{weather.get('temp', '')}°C")

        context_str = "\n".join(f"- {p}" for p in context_parts)

        prompt = (
            f"根据以下要求，推荐{count}首歌曲。\n"
            f"{context_str}\n\n"
            f"返回 JSON 数组，格式：\n"
            f'[{{"name": "歌曲名", "artist": "歌手", "reason": "推荐理由"}}]\n\n'
            f"只返回 JSON 数组，不要其他内容。"
        )

        messages = [
            {"role": "system", "content": "你是一个专业的音乐推荐助手，根据用户心情推荐歌曲。只返回 JSON。"},
            {"role": "user", "content": prompt},
        ]

        try:
            result = _call_llm(messages)
            start = result.find("[")
            end = result.rfind("]") + 1
            if start >= 0 and end > start:
                songs = json.loads(result[start:end])
                if isinstance(songs, list) and len(songs) > 0:
                    return songs[:count]
        except Exception as e:
            logger.warning("Mood playlist LLM failed: %s", e)

        # Fallback by mood
        fallbacks = {
            "轻松": [{"name": "阳光宅男", "artist": "周杰伦", "reason": "轻松愉快"}],
            "激烈": [{"name": "黄河大合唱", "artist": "中央乐团", "reason": "气势磅礴"}],
            "安静": [{"name": "星空", "artist": "久石让", "reason": "安静舒缓"}],
            "愉悦": [{"name": "阳光宅男", "artist": "周杰伦", "reason": "开心快乐"}],
            "悲伤": [{"name": "眼泪", "artist": "范晓萱", "reason": "深情忧郁"}],
            "浪漫": [{"name": "告白气球", "artist": "周杰伦", "reason": "浪漫甜蜜"}],
        }
        return fallbacks.get(mood, [{"name": "天空之城", "artist": "久石让", "reason": "推荐歌曲"}])