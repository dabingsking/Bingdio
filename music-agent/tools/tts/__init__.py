"""TTS tool using MiMo V2.5-TTS API."""

import base64
import os
import subprocess
import uuid
from typing import Any

import requests
import yaml

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "config.yaml")

E301 = "E301"  # Configuration error
E302 = "E302"  # API request error


def _load_config() -> dict[str, Any]:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _wsl_to_win_path(wsl_path: str) -> str:
    """Convert WSL path to Windows path."""
    try:
        return subprocess.check_output(
            ["wslpath", "-w", wsl_path], text=True
        ).strip()
    except Exception:
        return wsl_path


def speak_text(text: str, voice: str = "冰糖") -> dict[str, Any]:
    """Convert text to speech via MiMo TTS API.

    Args:
        text: The text to synthesize.
        voice: Voice ID (default: 冰糖)

    Returns:
        dict with keys: mp3_path (str), code (str)
        On error: code contains E301/E302 and msg describes the issue.
    """
    try:
        config = _load_config()
        llm_cfg = config.get("llm", {})
    except Exception as e:
        return {"code": E301, "msg": f"Failed to load config: {e}"}

    base_url = llm_cfg.get("base_url")
    
    # Check env vars first, then fall back to config file
    api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or llm_cfg.get("api_key", "")

    if not base_url:
        return {"code": E301, "msg": "Missing base_url in config"}

    if not api_key:
        return {"code": E301, "msg": "Missing API key (LLM_API_KEY or OPENAI_API_KEY)"}

    url = base_url.rstrip("/") + "/chat/completions"

    try:
        resp = requests.post(
            url,
            json={
                "model": "mimo-v2.5-tts",
                "messages": [
                    {"role": "user", "content": "用平静温和的语气朗读。"},
                    {"role": "assistant", "content": text},
                ],
                "audio": {"format": "wav", "voice": voice},
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        resp.encoding = "utf-8"
        resp.raise_for_status()
    except requests.RequestException as e:
        return {"code": E302, "msg": f"API request failed: {e}"}

    try:
        data = resp.json()
        audio_data = data["choices"][0]["message"]["audio"]["data"]
        audio_bytes = base64.b64decode(audio_data)
    except Exception as e:
        return {"code": E302, "msg": f"Failed to parse audio response: {e}"}

    output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "tmp")
    os.makedirs(output_dir, exist_ok=True)
    wav_path = os.path.join(output_dir, f"tts_{uuid.uuid4().hex}.wav")
    
    try:
        with open(wav_path, "wb") as f:
            f.write(audio_bytes)
    except Exception as e:
        return {"code": E302, "msg": f"Failed to write audio file: {e}"}

    # Windows 播放
    try:
        win_path = _wsl_to_win_path(wav_path)
        subprocess.run(
            ["cmd.exe", "/c",
             f"powershell.exe -ExecutionPolicy Bypass -Command "
             f"(New-Object System.Media.SoundPlayer('{win_path}')).PlaySync()"],
            timeout=30,
        )
    except Exception:
        pass

    return {"code": "0", "mp3_path": wav_path}
