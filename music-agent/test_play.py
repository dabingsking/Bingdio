"""Minimal test: can we get song URL and play with mpv?"""

import subprocess, json, requests

NCM = r"C:\Users\Administrator\AppData\Roaming\npm\ncm-cli.cmd"


def search(keyword, limit=3):
    r = subprocess.run(
        [NCM, "search", "song", "--keyword", keyword, "--limit", str(limit), "--output", "json"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20
    )
    data = json.loads(r.stdout)
    records = data.get("data", {}).get("records", [])
    return [{"name": x["name"], "enc_id": x["id"], "orig_id": x["originalId"],
             "artist": ",".join(a["name"] for a in x.get("artists", []))} for x in records]


def get_url(song_id):
    """Get song URL via netease API."""
    # Try via ncm-cli recommend first
    return None


# Test 1: search
print("=== Search ===")
songs = search("周杰伦 夜曲")
for s in songs:
    print(f"  {s['name']} - {s['artist']} | enc={s['enc_id'][:16]}")

# Test 2: play via ncm-cli
if songs:
    s = songs[0]
    print(f"\n=== Play {s['name']} ===")
    r = subprocess.run(
        [NCM, "play", "--song", "--encrypted-id", s["enc_id"], "--original-id", str(s["orig_id"])],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5
    )
    print(f"play stdout: {r.stdout[:200]}")
    print(f"play stderr: {r.stderr[:200]}")

# Test 3: check state
print("\n=== State ===")
r = subprocess.run([NCM, "state", "--output", "json"], capture_output=True, text=True, encoding="utf-8", errors="replace")
print(r.stdout[:300])