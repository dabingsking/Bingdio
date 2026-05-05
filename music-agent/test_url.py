"""Direct netease API to get song URL + mpv playback."""

import subprocess, json, base64, os, sys

# Check config for API keys
def load_config():
    import yaml
    cfg_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(cfg_path, encoding="utf-8") as f:
        return yaml.safe_load(f)

cfg = load_config()
app_cfg = cfg.get("netease_app", {})
app_id = app_cfg.get("app_id", "")
private_key = app_cfg.get("private_key", "")

print(f"app_id: {app_id[:10]}...")

# Encryption helpers
_MODULUS = "00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7"
_NONCE = "0CoJUm6Qyw8W8jud"
_PUBKEY = "010001"

def create_secret_key(size=16):
    import binascii
    return binascii.hexlify(os.urandom(size))[:size].decode("utf-8")

def aes_encrypt(text, key):
    from Crypto.Cipher import AES
    pad = 16 - len(text) % 16
    text = text + chr(pad) * pad
    encryptor = AES.new(key.encode("utf-8"), AES.MODE_CBC, b"0102030405060708")
    ciphertext = encryptor.encrypt(text.encode("utf-8"))
    return base64.b64encode(ciphertext).decode("utf-8").strip()

def rsa_encrypt(text, pub_key, modulus):
    import binascii
    reversed_text = text[::-1]
    bi_text = int(binascii.hexlify(reversed_text.encode("utf-8")), 16)
    bi_ex = int(pub_key, 16)
    bi_mod = int(modulus, 16)
    encrypted = pow(bi_text, bi_ex, bi_mod)
    return format(encrypted, "x").zfill(256)

def encrypt_request(data):
    text = json.dumps(data)
    sec_key = create_secret_key(16)
    enc_text = aes_encrypt(aes_encrypt(text, _NONCE), sec_key)
    enc_sec_key = rsa_encrypt(sec_key, _PUBKEY, _MODULUS)
    return {"params": enc_text, "encSecKey": enc_sec_key}

def get_song_url(song_id):
    """Get song URL via netease API."""
    url = "https://music.163.com/weapi/song/enhance/player/url/v1"
    params = {"ids": [song_id], "level": "standard", "encodeType": "aac", "csrf_token": ""}
    enc_data = encrypt_request(params)

    import requests
    resp = requests.post(
        url,
        data={"params": enc_data["params"], "encSecKey": enc_data["encSecKey"], "appid": app_id},
        headers={"Referer": "https://music.163.com", "User-Agent": "Mozilla/5.0"},
        timeout=10
    )
    resp.encoding = "utf-8"
    data = resp.json()
    if data.get("code") == 200:
        url_list = data.get("data", [])
        if url_list:
            return url_list[0].get("url", "")
    return None

def search_song(keyword):
    """Search via ncm-cli and return first song's IDs."""
    result = subprocess.run(
        [r"C:\Users\Administrator\AppData\Roaming\npm\ncm-cli.cmd", "search", "song", "--keyword", keyword, "--limit", "1", "--output", "json"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20
    )
    data = json.loads(result.stdout)
    records = data.get("data", {}).get("records", [])
    if records:
        r = records[0]
        return {"name": r["name"], "enc_id": r["id"], "orig_id": r["originalId"]}
    return None

# Test flow
print("=== Step 1: Search ===")
song = search_song("周杰伦 夜曲")
print(f"Found: {song}")

print("\n=== Step 2: Get URL ===")
if song:
    song_url = get_song_url(song["orig_id"])
    print(f"URL: {song_url[:80] if song_url else 'None'}")

    if song_url:
        print("\n=== Step 3: Play with mpv ===")
        mpv_path = r"C:\Users\Administrator\AppData\Roaming\npm\mpv.exe"
        # Try playing just audio
        result = subprocess.Popen(
            [mpv_path, "--no-video", "--really-quiet", song_url],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        print(f"mpv started with PID: {result.pid}")
        import time
        time.sleep(5)
        result.terminate()
        result.wait()
        print("mpv finished")