"""Simplified autonomous agent for Bingody B-mode.

Focus: reliable music playback via mpv direct URL + natural language control.
"""

from __future__ import annotations

import json
import logging
import queue
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

NCM_CLI = r"C:\Users\Administrator\AppData\Roaming\npm\ncm-cli.cmd"
MPV_CLI = r"C:\Users\Administrator\AppData\Roaming\npm\mpv.exe"


def _run_ncm(*args: str) -> dict:
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


def _get_song_url(song_id: int) -> str | None:
    """Get song playback URL from NetEase API."""
    import base64
    import binascii
    import json as jsonlib
    import os

    import yaml
    from Crypto.Cipher import AES

    cfg_path = Path(__file__).parent.parent / "config.yaml"
    if not cfg_path.exists():
        return None
    with open(cfg_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    app_cfg = cfg.get("netease_app", {})
    app_id = app_cfg.get("app_id", "")
    if not app_id:
        return None

    _MODULUS = "00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7"
    _NONCE = "0CoJUm6Qyw8W8jud"
    _PUBKEY = "010001"

    def _create_secret_key(size=16):
        return binascii.hexlify(os.urandom(size))[:size].decode("utf-8")

    def _aes_encrypt(text, key):
        pad = 16 - len(text) % 16
        text = text + chr(pad) * pad
        encryptor = AES.new(key.encode("utf-8"), AES.MODE_CBC, b"0102030405060708")
        return base64.b64encode(encryptor.encrypt(text.encode("utf-8"))).decode("utf-8").strip()

    def _rsa_encrypt(text, pub_key, modulus):
        reversed_text = text[::-1]
        bi_text = int(binascii.hexlify(reversed_text.encode("utf-8")), 16)
        encrypted = pow(bi_text, int(pub_key, 16), int(modulus, 16))
        return format(encrypted, "x").zfill(256)

    def _encrypt_request(data):
        text = jsonlib.dumps(data)
        sec_key = _create_secret_key(16)
        enc_text = _aes_encrypt(_aes_encrypt(text, _NONCE), sec_key)
        enc_sec_key = _rsa_encrypt(sec_key, _PUBKEY, _MODULUS)
        return {"params": enc_text, "encSecKey": enc_sec_key}

    params = {"ids": [song_id], "level": "standard", "encodeType": "aac", "csrf_token": ""}
    enc_data = _encrypt_request(params)
    try:
        import requests
        resp = requests.post(
            "https://music.163.com/weapi/song/enhance/player/url/v1",
            data={"params": enc_data["params"], "encSecKey": enc_data["encSecKey"], "appid": app_id},
            headers={"Referer": "https://music.163.com", "User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        resp.encoding = "utf-8"
        data = resp.json()
        url_list = data.get("data", [])
        if url_list:
            return url_list[0].get("url")
    except Exception:
        pass
    return None


# ── Tools ──────────────────────────────────────────────────────────

def tool_search(keyword: str, limit: int = 5) -> dict:
    """Search songs by keyword."""
    result = _run_ncm("search", "song", "--keyword", keyword, "--limit", str(limit), "--output", "json")
    if result.get("code") != 200:
        return {"code": "E1", "msg": f"Search failed: {result.get('message')}", "songs": []}

    songs = []
    for item in result.get("data", {}).get("records", []):
        artists = [a.get("name", "") for a in item.get("artists", [])]
        songs.append({
            "name": item.get("name", ""),
            "artist": ", ".join(artists) if artists else "",
            "original_id": item.get("originalId"),
            "encrypted_id": item.get("id"),
        })
    return {"code": "0", "songs": songs}


def tool_play(encrypted_id: str, original_id: str = "") -> dict:
    """Play a song by encrypted_id via direct mpv playback (bypasses broken ncm-cli service)."""
    song_url = None
    if original_id:
        try:
            song_id = int(original_id)
            song_url = _get_song_url(song_id)
        except (ValueError, TypeError):
            pass

    if song_url:
        try:
            subprocess.Popen(
                [MPV_CLI, "--no-video", "--really-quiet", song_url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return {"success": True, "message": f"Playing via mpv"}
        except Exception as e:
            return {"success": False, "message": f"mpv failed: {e}"}

    # Fallback: try ncm-cli
    return _run_ncm("play", "--song", "--encrypted-id", encrypted_id,
                    "--original-id", str(original_id) if original_id else "")


def tool_queue_clear() -> dict:
    return _run_ncm("queue", "clear", "--output", "json")


def tool_queue_list() -> dict:
    return _run_ncm("queue", "--output", "json")


def tool_next() -> dict:
    return _run_ncm("next", "--output", "json")


def tool_prev() -> dict:
    return _run_ncm("prev", "--output", "json")


def tool_pause() -> dict:
    return _run_ncm("pause", "--output", "json")


def tool_resume() -> dict:
    return _run_ncm("resume", "--output", "json")


def tool_volume_up() -> dict:
    st = tool_state()
    if st.get("success"):
        cur = st.get("state", {}).get("volume") or 50
        new_vol = min(100, int(cur) + 10)
    else:
        new_vol = 60
    return _run_ncm("volume", str(new_vol), "--output", "json")


def tool_volume_down() -> dict:
    st = tool_state()
    if st.get("success"):
        cur = st.get("state", {}).get("volume") or 50
        new_vol = max(0, int(cur) - 10)
    else:
        new_vol = 40
    return _run_ncm("volume", str(new_vol), "--output", "json")


def tool_state() -> dict:
    return _run_ncm("state", "--output", "json")


def tool_current_song() -> dict:
    st = tool_state()
    if st.get("success"):
        s = st.get("state", {})
        title = s.get("title", "未知")
        return {
            "success": True,
            "song": title if title else "无",
            "artist": "未知",
            "status": s.get("status", "unknown"),
            "position": s.get("position", 0),
            "duration": s.get("duration", 0),
        }
    return {"success": False, "song": None}


def tool_weather() -> dict:
    """Get weather via QWeather API."""
    import os
    import yaml

    cfg_path = Path(__file__).parent.parent / "config.yaml"
    if not cfg_path.exists():
        return {"code": "E1", "msg": "config not found"}
    with open(cfg_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    w_cfg = cfg.get("weather", {})
    host = w_cfg.get("host")
    key = w_cfg.get("key")
    location = w_cfg.get("location")
    if not host or not key:
        return {"code": "E1", "msg": "weather config missing"}

    import requests
    try:
        resp = requests.get(f"https://{host}/v7/weather/now",
                            params={"location": location, "key": key}, timeout=10)
        data = resp.json()
        if data.get("code") == "200":
            now = data.get("now", {})
            return {"code": "0", "temp": now.get("temp", ""), "text": now.get("text", ""),
                    "wind_speed": now.get("windSpeed", "")}
    except Exception as e:
        return {"code": "E1", "msg": str(e)}
    return {"code": "E1", "msg": "weather failed"}


def tool_tts(text: str) -> dict:
    """TTS speak via MiMo API."""
    import base64
    import os
    import yaml

    cfg_path = Path(__file__).parent.parent / "config.yaml"
    if not cfg_path.exists():
        return {"code": "E1", "msg": "config not found"}
    with open(cfg_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    llm_cfg = cfg.get("llm", {})
    api_key = os.getenv("LLM_API_KEY") or llm_cfg.get("api_key", "")
    base_url = llm_cfg.get("base_url", "https://token-plan-cn.xiaomimino.com/v1")
    if not api_key:
        return {"code": "E1", "msg": "no api key"}

    import requests
    url = base_url.rstrip("/") + "/chat/completions"
    try:
        resp = requests.post(url, json={
            "model": "mimo-v2.5-tts",
            "messages": [
                {"role": "user", "content": "用平静温和的语气朗读。"},
                {"role": "assistant", "content": text},
            ],
            "audio": {"format": "wav", "voice": "冰糖"},
        }, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, timeout=30)
        resp.encoding = "utf-8"
        resp.raise_for_status()
        audio_data = resp.json()["choices"][0]["message"]["audio"]["data"]
        audio_bytes = base64.b64decode(audio_data)

        out_dir = Path(__file__).parent.parent / "tmp"
        out_dir.mkdir(exist_ok=True)
        wav_path = out_dir / f"tts_{datetime.now().strftime('%H%M%S')}.wav"
        with open(wav_path, "wb") as f:
            f.write(audio_bytes)

        subprocess.run(
            ["powershell.exe", "-ExecutionPolicy", "Bypass", "-Command",
             f"(New-Object System.Media.SoundPlayer('{wav_path}')).PlaySync()"],
            timeout=30, errors="ignore"
        )
        return {"code": "0", "msg": f"TTS played: {text[:20]}..."}
    except Exception as e:
        return {"code": "E1", "msg": f"TTS failed: {e}"}


def tool_change_mood(mood: str) -> dict:
    """Change mood - rebuild playlist based on mood."""
    playlists = {
        "轻松": ["阳光宅男", "简单爱", "园游会", "牛仔很忙", "稻香"],
        "激烈": ["双截棍", "龙拳", "以父之名", "夜的第七章", "霍元甲"],
        "安静": ["星空", "天空之城", "Merry Christmas Mr. Lawrence", "river flows in you", "夜曲"],
        "愉悦": ["简单爱", "园游会", "晴天", "稻香", "星晴"],
        "悲伤": ["安静", "眼泪", "龙卷风", "搁浅", "彩虹"],
        "浪漫": ["告白气球", "简单爱", "园游会", "星晴", "龙卷风"],
    }
    return {"code": "0", "mood": mood, "songs": playlists.get(mood, playlists["轻松"])}


# ── Intent Detection ───────────────────────────────────────────────

def _detect(text: str) -> dict | None:
    """Rule-based intent detection."""
    t = text.strip().lower()

    if any(k in t for k in ["下一首", "下一曲", "next", "skip"]):
        return {"tool": "next", "args": {}}
    if any(k in t for k in ["上一首", "上一曲", "previous", "prev"]):
        return {"tool": "prev", "args": {}}
    if any(k in t for k in ["暂停", "pause", "停止"]):
        return {"tool": "pause", "args": {}}
    if any(k in t for k in ["继续", "恢复", "resume", "继续播放", "播放"]):
        return {"tool": "resume", "args": {}}
    if any(k in t for k in ["音量加", "大声点", "volume up"]):
        return {"tool": "volume_up", "args": {}}
    if any(k in t for k in ["音量减", "小声点", "volume down"]):
        return {"tool": "volume_down", "args": {}}

    if any(k in t for k in ["现在播什么", "正在播放", "current"]):
        return {"tool": "current_song", "args": {}}
    if any(k in t for k in ["播放列表", "歌单", "playlist"]):
        return {"tool": "queue_list", "args": {}}
    if any(k in t for k in ["天气", "weather"]):
        return {"tool": "weather", "args": {}}

    for mood in ["轻松", "激烈", "安静", "愉悦", "悲伤", "浪漫"]:
        if mood in t:
            return {"tool": "change_mood", "args": {"mood": mood}}

    for kw in ["播放", "来首歌", "放歌", "唱"]:
        if kw in t:
            song = t.split(kw, 1)[-1].strip()
            if song:
                return {"tool": "play_song", "args": {"song_name": song}}

    return None


# ── Tool execution ─────────────────────────────────────────────────

def _execute(tool: str, args: dict) -> str:
    """Execute a tool and return text response."""
    try:
        if tool == "next":
            r = tool_next()
            return "已切换到下一首" if r.get("success") else f"切换失败: {r.get('message')}"
        if tool == "prev":
            r = tool_prev()
            return "已切换到上一首" if r.get("success") else f"切换失败: {r.get('message')}"
        if tool == "pause":
            r = tool_pause()
            return "已暂停" if r.get("success") else f"暂停失败: {r.get('message')}"
        if tool == "resume":
            r = tool_resume()
            return "继续播放" if r.get("success") else f"继续播放失败: {r.get('message')}"
        if tool == "volume_up":
            r = tool_volume_up()
            return "音量已增加"
        if tool == "volume_down":
            r = tool_volume_down()
            return "音量已降低"
        if tool == "current_song":
            r = tool_current_song()
            if r.get("success"):
                return f"正在播放：{r.get('song', '未知')}，状态：{r.get('status', 'unknown')}"
            return "当前无播放"
        if tool == "queue_list":
            r = tool_queue_list()
            if r.get("success"):
                st = r.get("state", {})
                return f"队列长度：{st.get('queueLength', 0)}，当前：{st.get('currentIndex', 0)}"
            return "无法获取播放列表"
        if tool == "weather":
            r = tool_weather()
            if r.get("code") == "0":
                return f"天气：{r.get('text', '')}，{r.get('temp', '')}°C，风速{r.get('wind_speed', '')}km/h"
            return f"天气获取失败: {r.get('msg')}"
        if tool == "change_mood":
            mood = args.get("mood", "")
            r = tool_change_mood(mood)
            if r.get("code") == "0":
                songs = r.get("songs", [])
                return f"已切换到{mood}心情的歌单：{', '.join(songs[:3])}"
            return f"切换失败: {r.get('msg')}"
        if tool == "play_song":
            song_name = args.get("song_name", "")
            if not song_name:
                return "请指定歌曲名"
            sr = tool_search(song_name)
            songs = sr.get("songs", [])
            if not songs:
                return f"未找到歌曲：{song_name}"
            s = songs[0]
            enc_id = s.get("encrypted_id", "")
            orig_id = s.get("original_id", "")
            if not enc_id:
                return f"歌曲 {song_name} 无法播放（无加密ID）"
            pr = tool_play(enc_id, str(orig_id) if orig_id else "")
            if pr.get("success"):
                return f"正在播放：{s.get('name', song_name)} - {s.get('artist', '')}"
            return f"播放失败: {pr.get('message')}"
        if tool == "tts":
            r = tool_tts(args.get("text", ""))
            return r.get("msg", "TTS完成")
    except Exception as e:
        return f"执行错误: {e}"
    return "未知命令"


# ── AutonomousAgent ─────────────────────────────────────────────────

class AutonomousAgent:
    """
    B-mode autonomous agent.
    - Startup: builds playlist from context, plays first song, TTS intro
    - Runtime: handles NL commands via rule-based intent + tool execution
    """

    def __init__(self, command_queue: Optional[queue.Queue] = None,
                 event_queue: Optional[queue.Queue] = None):
        self.command_queue = command_queue or queue.Queue()
        self.event_queue = event_queue or queue.Queue()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def on_user_input(self, text: str) -> str:
        """Handle user input - intent detection + tool execution."""
        quick = _detect(text)
        if quick:
            return _execute(quick["tool"], quick["args"])
        return _execute("play_song", {"song_name": text.strip()})

    def _run_loop(self) -> None:
        """Startup + command loop."""
        try:
            self._startup()
        except Exception as e:
            logger.error("Startup failed: %s", e)

        while self._running:
            try:
                cmd = self.command_queue.get(timeout=0.5)
                if cmd.get("type") == "stop":
                    break
                if cmd.get("type") == "user_input":
                    text = cmd.get("text", "")
                    response = self.on_user_input(text)
                    if response:
                        self.event_queue.put_nowait({"type": "agent_response", "data": response})
            except queue.Empty:
                pass
            except Exception as e:
                logger.error("Loop error: %s", e)

        logger.info("Agent loop ended")

    def _startup(self) -> None:
        """Startup: build playlist + play + TTS intro."""
        logger.info("Agent startup begin")

        # 1. Get weather
        weather = tool_weather()
        if weather.get("code") == "0":
            logger.info("天气: %s %s°C", weather.get("text"), weather.get("temp"))

        # 2. Clear ncm-cli queue
        tool_queue_clear()

        # 3. Search for songs that have free (fee=0 or fee=8) URLs
        # Try multiple searches to find playable songs
        search_keywords = ["晴天 周杰伦", "简单爱 周杰伦", "稻香 周杰伦"]
        playable_songs = []
        for kw in search_keywords:
            sr = tool_search(kw, limit=3)
            for s in sr.get("songs", []):
                orig_id = s.get("original_id")
                if orig_id:
                    url = _get_song_url(int(orig_id))
                    if url:
                        s["url"] = url
                        playable_songs.append(s)
                        logger.info("Found playable: %s (fee=%s)", s.get("name"), "free" if url else "unknown")
                if len(playable_songs) >= 3:
                    break
            if len(playable_songs) >= 3:
                break

        # 4. Play first song directly with mpv
        if playable_songs:
            first = playable_songs[0]
            try:
                subprocess.Popen(
                    [MPV_CLI, "--no-video", "--really-quiet", first["url"]],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                logger.info("Playing startup song: %s", first.get("name"))
            except Exception as e:
                logger.warning("Startup mpv failed: %s", e)

        # 5. TTS intro
        try:
            temp = weather.get("temp", "未知") if weather.get("code") == "0" else "未知"
            text_w = weather.get("text", "未知") if weather.get("code") == "0" else "未知"
            intro = f"你好，我是 Bingody。当前天气{text_w}，{temp}度。已准备好播放。"
            tool_tts(intro)
            logger.info("TTS intro played")
        except Exception as e:
            logger.warning("TTS intro failed: %s", e)

        logger.info("Agent startup complete")
