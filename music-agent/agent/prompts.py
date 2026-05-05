"""System prompts for Bingody agent tool-calling mode."""

from typing import Any


def build_system_prompt(
    current_song: dict | None = None,
    playlist: list[dict] | None = None,
    weather: dict | None = None,
    time_of_day: str = "晚上",
) -> str:
    """
    Build the system prompt for tool-calling agent mode.

    Args:
        current_song: Currently playing song info
        playlist: Current playlist (list of song dicts)
        weather: Current weather info
        time_of_day: Time period (早上/下午/晚上)

    Returns:
        System prompt string
    """
    # Format current song
    if current_song:
        song_info = f"正在播放：{current_song.get('song', '未知')} - {current_song.get('artist', '未知')}"
    else:
        song_info = "当前无播放"

    # Format playlist summary
    if playlist:
        names = [s.get("name", "?") for s in playlist[:5]]
        remaining = len(playlist) - 5
        playlist_info = f"播放列表（{len(playlist)}首）：{', '.join(names)}"
        if remaining > 0:
            playlist_info += f" 等{remaining}首"
    else:
        playlist_info = "播放列表为空"

    # Format weather
    if weather and weather.get("code") == "0":
        weather_info = f"天气：{weather.get('text', '')}，{weather.get('temp', '')}°C"
    else:
        weather_info = "天气：未知"

    # Build tool descriptions
    tool_desc = []
    for tool in _TOOL_DESCRIPTIONS:
        tool_desc.append(f"- {tool['name']}: {tool['description']}")

    return f"""你是一个音乐智能体助手 Bingody。你可以通过调用工具来控制音乐播放。

当前状态：
- {song_info}
- {playlist_info}
- {weather_info}
- 时间段：{time_of_day}

可用工具：
{chr(10).join(tool_desc)}

指令要求：
1. 用户用自然语言提出请求时，选择最合适的工具来响应
2. 直接输出JSON格式的工具调用指令，不要有多余的解释
3. 如果用户的请求不需要调用工具，可以用文字回复
4. 重要反馈可以使用 speak 工具通过TTS播报

工具调用格式：
{{"tool": "工具名", "args": {{"参数名": "参数值"}}}}

示例：
用户: 播放周杰伦的歌
输出: {{"tool": "play_song", "args": {{"song_id": "周杰伦"}}}}"

用户: 天气怎么样
输出: {{"tool": "get_weather", "args": {{}}}}"""

    # 用户: 下一首
# 输出: {{"tool": "next_song", "args": {{}}}}"""


# Tool descriptions (for prompt)
_TOOL_DESCRIPTIONS = [
    {"name": "search_song", "description": "搜索歌曲，参数：keyword(歌曲名), limit(数量，默认5)"},
    {"name": "play_song", "description": "播放歌曲，参数：song_id(歌曲名、加密ID或搜索关键词)"},
    {"name": "get_current_song", "description": "获取当前播放的歌曲信息"},
    {"name": "next_song", "description": "跳转到下一首"},
    {"name": "prev_song", "description": "跳转到上一首"},
    {"name": "pause", "description": "暂停播放"},
    {"name": "resume", "description": "继续播放"},
    {"name": "volume_up", "description": "增加音量"},
    {"name": "volume_down", "description": "降低音量"},
    {"name": "get_weather", "description": "获取当前天气"},
    {"name": "get_lyric", "description": "获取歌词，参数：song_id"},
    {"name": "add_mood_log", "description": "记录心情，参数：mood_label(标签), mood_score(分数-1到1), context(上下文)"},
    {"name": "speak", "description": "TTS播报，参数：text(文本), voice(音色，默认冰糖)"},
    {"name": "change_mood", "description": "改变歌单心情，参数：mood(轻松/激烈/安静/愉悦/悲伤/浪漫)"},
    {"name": "get_playlist", "description": "获取当前播放列表信息"},
]
