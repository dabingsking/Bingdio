"""Weather tool using QWeather API v7."""

import os
from typing import Any

import requests
import yaml

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "config.yaml")

E101 = "E101"  # Configuration error
E102 = "E102"  # API request error


def _load_config() -> dict[str, Any]:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_weather() -> dict[str, Any]:
    """Fetch current weather data from QWeather API v7.

    Returns:
        dict with keys: temp (str), text (str), wind_speed (str), humidity (str), code (str)
        On error: code contains E101/E102 and msg describes the issue.
    """
    try:
        config = _load_config()
        weather_cfg = config.get("weather", {})
    except Exception:
        return {"code": E101, "msg": "Failed to load weather config"}

    host = weather_cfg.get("host")
    key = weather_cfg.get("key")
    location = weather_cfg.get("location")

    if not host or not key or not location:
        return {"code": E101, "msg": "Missing weather config: host/key/location"}

    url = f"https://{host}/v7/weather/now"

    try:
        resp = requests.get(url, params={"location": location, "key": key}, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        return {"code": E102, "msg": f"API request failed: {e}"}

    data = resp.json()
    code = data.get("code", "")
    if code != "200":
        return {"code": E102, "msg": f"API error: code={code}"}

    now = data.get("now", {})
    return {
        "code": "0",
        "temp": now.get("temp", ""),
        "text": now.get("text", ""),
        "wind_speed": now.get("windSpeed", ""),
        "humidity": now.get("humidity", ""),
    }
