"""Netease Cloud Music tool using ncm-cli."""

import os
import json
import random
import subprocess
import binascii
from typing import Any

import requests
import yaml
from Crypto.Cipher import AES


CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "config.yaml")
NCM_CLI = "C:\\Users\\Administrator\\AppData\\Roaming\\npm\\ncm-cli.cmd"

E201 = "E201"  # Configuration error
E202 = "E202"  # API request/playback error

# NetEase encryption constants
_MODULUS = (
    "00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7"
    "b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280"
    "104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932"
    "575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b"
    "3ece0462db0a22b8e7"
)
_NONCE = "0CoJUm6Qyw8W8jud"
_PUBKEY = "010001"


_config_cache: dict[str, Any] | None = None


def _load_config() -> dict[str, Any]:
    """Load configuration from config.yaml."""
    global _config_cache
    if _config_cache is None:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            _config_cache = yaml.safe_load(f)
    return _config_cache


def _get_app_config() -> dict[str, str]:
    """Get NetEase app config from config.yaml."""
    config = _load_config()
    app_cfg = config.get("netease_app", {})
    if not app_cfg.get("app_id") or not app_cfg.get("private_key"):
        raise ValueError("Missing netease_app.app_id or private_key in config")
    return app_cfg


def _create_secret_key(size: int = 16) -> str:
    """Generate random secret key."""
    return binascii.hexlify(os.urandom(size))[:size].decode("utf-8")


def _aes_encrypt(text: str, key: str) -> str:
    """AES CBC encryption."""
    pad = 16 - len(text) % 16
    text = text + chr(pad) * pad
    encryptor = AES.new(key.encode("utf-8"), AES.MODE_CBC, b"0102030405060708")
    ciphertext = encryptor.encrypt(text.encode("utf-8"))
    return binascii.b2a_base64(ciphertext).decode("utf-8").strip()


def _rsa_encrypt(text: str, pub_key: str, modulus: str) -> str:
    """RSA encryption with reversed text."""
    reversed_text = text[::-1]
    bi_text = int(binascii.hexlify(reversed_text.encode("utf-8")), 16)
    bi_ex = int(pub_key, 16)
    bi_mod = int(modulus, 16)
    encrypted = pow(bi_text, bi_ex, bi_mod)
    return format(encrypted, "x").zfill(256)


def _encrypt_request(data: dict, pub_key: str = _PUBKEY, modulus: str = _MODULUS) -> dict:
    """Generate encrypted request params for NetEase API."""
    text = json.dumps(data)
    sec_key = _create_secret_key(16)
    enc_text = _aes_encrypt(_aes_encrypt(text, _NONCE), sec_key)
    enc_sec_key = _rsa_encrypt(sec_key, pub_key, modulus)
    return {"params": enc_text, "encSecKey": enc_sec_key}


def search_song(keywords: str, limit: int = 10) -> dict[str, Any]:
    """Search for songs using ncm-cli.

    Args:
        keywords: Search keywords
        limit: Maximum number of results (default 10)

    Returns:
        dict with keys: code (str), songs (list), msg (str, on error)
    """
    try:
        result = subprocess.run(
            [NCM_CLI, "search", "song", "--keyword", keywords, "--limit", str(limit)],
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
            errors="replace",
        )
        data = json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        return {"code": E202, "msg": "Search timeout"}
    except (json.JSONDecodeError, FileNotFoundError) as e:
        return {"code": E202, "msg": f"Search failed: {e}"}

    if data.get("code") != 200:
        return {"code": E202, "msg": f"Search error: {data.get('message')}"}

    songs = []
    for item in data.get("data", {}).get("records", []):
        songs.append({
            "id": item.get("originalId"),
            "encrypted_id": item.get("id"),
            "name": item.get("name"),
            "artists": [a.get("name") for a in item.get("artists", [])],
            "album": item.get("album", {}).get("name", "") if item.get("album") else "",
            "duration": item.get("duration", 0),
        })
    return {"code": "0", "songs": songs}


def get_song_detail(song_id: int | str) -> dict[str, Any]:
    """Get song detail including encrypted ID using NetEase API.

    Args:
        song_id: Netease song ID

    Returns:
        dict with keys: code (str), song (dict with id, encrypted_id), msg (str, on error)
    """
    try:
        app_cfg = _get_app_config()
    except Exception as e:
        return {"code": E201, "msg": f"Configuration error: {e}"}

    app_id = app_cfg["app_id"]
    private_key = app_cfg["private_key"]

    url = "https://music.163.com/api/song/detail/v2"
    params = {"ids": [song_id], "appid": app_id, "type": "1"}
    enc_data = _encrypt_request(params, _PUBKEY, _MODULUS)

    try:
        resp = requests.post(
            url,
            data={
                "params": enc_data["params"],
                "encSecKey": enc_data["encSecKey"],
                "appid": app_id,
            },
            headers={
                "Referer": "https://music.163.com",
                "User-Agent": "Mozilla/5.0",
            },
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        return {"code": E202, "msg": f"API request failed: {e}"}

    data = resp.json()
    if data.get("code") != 200:
        return {"code": E202, "msg": f"API error: {data.get('message', data.get('msg'))}"}

    song_data = data.get("songs", [{}])[0]
    return {
        "code": "0",
        "song": {
            "id": song_data.get("id"),
            "encrypted_id": song_data.get("encryptId", ""),
            "name": song_data.get("name"),
        }
    }


def get_url(song_id: int | str) -> dict[str, Any]:
    """Get song playback URL.

    Args:
        song_id: Netease song ID

    Returns:
        dict with keys: code (str), url (str), msg (str, on error)
    """
    try:
        app_cfg = _get_app_config()
    except Exception as e:
        return {"code": E201, "msg": f"Configuration error: {e}"}

    app_id = app_cfg["app_id"]
    url = "https://music.163.com/weapi/song/enhance/player/url/v1"
    params = {"ids": [song_id], "level": "standard", "encodeType": "aac", "csrf_token": ""}
    enc_data = _encrypt_request(params)

    try:
        resp = requests.post(
            url,
            data={
                "params": enc_data["params"],
                "encSecKey": enc_data["encSecKey"],
                "appid": app_id,
            },
            headers={
                "Referer": "https://music.163.com",
                "User-Agent": "Mozilla/5.0",
            },
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        return {"code": E202, "msg": f"API request failed: {e}"}

    data = resp.json()
    if data.get("code") != 200:
        return {"code": E202, "msg": f"API error: {data.get('message', data.get('msg'))}"}

    url_list = data.get("data", [])
    if not url_list:
        return {"code": E202, "msg": "No URL available for this song"}

    return {"code": "0", "url": url_list[0].get("url", "")}


def get_lyric(song_id: int | str) -> dict[str, Any]:
    """Get song lyric.

    Args:
        song_id: Netease song ID

    Returns:
        dict with keys: code (str), lyric (str), msg (str, on error)
    """
    try:
        app_cfg = _get_app_config()
    except Exception as e:
        return {"code": E201, "msg": f"Configuration error: {e}"}

    app_id = app_cfg["app_id"]
    url = "https://music.163.com/api/song/lyric/v2"
    params = {"id": song_id, "type": 1}
    enc_data = _encrypt_request(params)

    try:
        resp = requests.post(
            url,
            data={
                "params": enc_data["params"],
                "encSecKey": enc_data["encSecKey"],
                "appid": app_id,
            },
            headers={
                "Referer": "https://music.163.com",
                "User-Agent": "Mozilla/5.0",
            },
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        return {"code": E202, "msg": f"API request failed: {e}"}

    data = resp.json()
    if data.get("code") != 200:
        return {"code": E202, "msg": f"API error: {data.get('message', data.get('msg'))}"}

    lrc = data.get("lrc", {}).get("lyric", "")
    return {"code": "0", "lyric": lrc}


def get_playlist(playlist_id: int | str) -> dict[str, Any]:
    """Get playlist details.

    Args:
        playlist_id: Netease playlist ID

    Returns:
        dict with keys: code (str), playlist (dict), msg (str, on error)
    """
    try:
        base_url = _get_base_url()
    except Exception as e:
        return {"code": E201, "msg": f"Configuration error: {e}"}

    url = f"{base_url}/playlist/detail"
    params = {"id": playlist_id}

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        return {"code": E202, "msg": f"API request failed: {e}"}

    data = resp.json()
    if data.get("code") != 200:
        return {"code": E202, "msg": f"API error: code={data.get('code')}"}

    playlist_info = data.get("playlist", {})
    tracks = []
    for item in playlist_info.get("tracks", []):
        tracks.append({
            "id": item.get("id"),
            "name": item.get("name"),
            "artists": [a.get("name") for a in item.get("ar", [])],
            "album": item.get("al", {}).get("name", ""),
        })

    return {
        "code": "0",
        "playlist": {
            "id": playlist_info.get("id"),
            "name": playlist_info.get("name"),
            "description": playlist_info.get("description", ""),
            "tracks": tracks,
        }
    }


def _get_base_url() -> str:
    """Get netease API base URL from config."""
    config = _load_config()
    netease_cfg = config.get("netease", {})
    base_url = netease_cfg.get("base_url")
    if not base_url:
        raise ValueError("Missing netease.base_url in config")
    return base_url


def play_song(song_id: int | str) -> dict[str, Any]:
    """Play a song using ncm-cli.

    Args:
        song_id: Can be:
            - A 32-char encrypted ID (hex string) - plays directly
            - A song name/keyword - searches and plays first result

    Returns:
        dict with keys: code (str), msg (str)
    """
    # Check if it's already an encrypted ID (32-char hex)
    song_id_str = str(song_id)
    if len(song_id_str) == 32 and all(c in "0123456789ABCDEF" for c in song_id_str.upper()):
        encrypted_id = song_id_str
    else:
        # Treat as search keyword
        search_result = search_song(song_id_str, limit=1)
        if search_result.get("code") != "0":
            return search_result

        songs = search_result.get("songs", [])
        if not songs:
            return {"code": E202, "msg": "Song not found"}

        encrypted_id = songs[0].get("encrypted_id")
        if not encrypted_id:
            return {"code": E202, "msg": "Failed to get encrypted song ID"}

    try:
        subprocess.run(
            [NCM_CLI, "queue", "add", "--encrypted-id", encrypted_id],
            timeout=300,
            check=True,
        )
    except subprocess.TimeoutExpired:
        return {"code": E202, "msg": "Playback timeout"}
    except FileNotFoundError:
        return {"code": E202, "msg": "ncm-cli not found"}
    except subprocess.CalledProcessError as e:
        return {"code": E202, "msg": f"Playback failed: {e}"}

    return {"code": "0", "msg": "Playback started"}


def get_url(song_id: int | str) -> dict[str, Any]:
    """Get song playback URL.

    Args:
        song_id: Netease song ID

    Returns:
        dict with keys: code (str), url (str), msg (str, on error)
    """
    try:
        base_url = _get_base_url()
    except Exception as e:
        return {"code": E201, "msg": f"Configuration error: {e}"}

    url = f"{base_url}/song/url"
    params = {"id": song_id}

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        return {"code": E202, "msg": f"API request failed: {e}"}

    data = resp.json()
    if data.get("code") != 200:
        return {"code": E202, "msg": f"API error: code={data.get('code')}"}

    url_list = data.get("data", [])
    if not url_list:
        return {"code": E202, "msg": "No URL available for this song"}

    return {"code": "0", "url": url_list[0].get("url", "")}


def get_lyric(song_id: int | str) -> dict[str, Any]:
    """Get song lyric.

    Args:
        song_id: Netease song ID

    Returns:
        dict with keys: code (str), lyric (str), msg (str, on error)
    """
    try:
        base_url = _get_base_url()
    except Exception as e:
        return {"code": E201, "msg": f"Configuration error: {e}"}

    url = f"{base_url}/lyric"
    params = {"id": song_id}

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        return {"code": E202, "msg": f"API request failed: {e}"}

    data = resp.json()
    if data.get("code") != 200:
        return {"code": E202, "msg": f"API error: code={data.get('code')}"}

    lrc = data.get("lrc", {}).get("lyric", "")
    return {"code": "0", "lyric": lrc}


def get_playlist(playlist_id: int | str) -> dict[str, Any]:
    """Get playlist details.

    Args:
        playlist_id: Netease playlist ID

    Returns:
        dict with keys: code (str), playlist (dict), msg (str, on error)
    """
    try:
        base_url = _get_base_url()
    except Exception as e:
        return {"code": E201, "msg": f"Configuration error: {e}"}

    url = f"{base_url}/playlist/detail"
    params = {"id": playlist_id}

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        return {"code": E202, "msg": f"API request failed: {e}"}

    data = resp.json()
    if data.get("code") != 200:
        return {"code": E202, "msg": f"API error: code={data.get('code')}"}

    playlist_info = data.get("playlist", {})
    tracks = []
    for item in playlist_info.get("tracks", []):
        tracks.append({
            "id": item.get("id"),
            "name": item.get("name"),
            "artists": [a.get("name") for a in item.get("ar", [])],
            "album": item.get("al", {}).get("name", ""),
        })

    return {
        "code": "0",
        "playlist": {
            "id": playlist_info.get("id"),
            "name": playlist_info.get("name"),
            "description": playlist_info.get("description", ""),
            "tracks": tracks,
        }
    }
