import os
import base64
import time
import re
import requests
from dotenv import load_dotenv

load_dotenv()

CID = os.getenv("SPOTIFY_CLIENT_ID")
CS = os.getenv("SPOTIFY_CLIENT_SECRET")
RT = os.getenv("SPOTIFY_REFRESH_TOKEN")

if not all([CID, CS, RT]):
    raise RuntimeError("Spotify env vars missing")


def get_token():
    auth = base64.b64encode(f"{CID}:{CS}".encode()).decode()
    r = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "refresh_token", "refresh_token": RT},
        headers={"Authorization": f"Basic {auth}"},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def normalize(t):
    return re.sub(r"[^a-z0-9]", "", t.lower())


def search(headers, q):
    r = requests.get(
        "https://api.spotify.com/v1/search",
        headers=headers,
        params={"q": q, "type": "track", "limit": 1},
        timeout=10,
    )
    if r.status_code != 200:
        return None
    items = r.json().get("tracks", {}).get("items", [])
    if not items:
        return None
    t = items[0]
    return {
        "uri": t["uri"],
        "song": t["name"],
        "artist": t["artists"][0]["name"],
    }


def verify(req, sp):
    if normalize(req["artist"]) == normalize(sp["artist"]) and normalize(req["song"]) == normalize(sp["song"]):
        return True, "exact"
    if normalize(req["artist"]) == normalize(sp["artist"]):
        return True, "title_variant"
    if normalize(req["song"]) == normalize(sp["song"]):
        return True, "track_only"
    return False, "reject"


def create_playlist(title, description, tracks, banned, target_count):
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    user = requests.get("https://api.spotify.com/v1/me", headers=headers).json()
    playlist = requests.post(
        f"https://api.spotify.com/v1/users/{user['id']}/playlists",
        headers={**headers, "Content-Type": "application/json"},
        json={"name": title, "description": description, "public": False},
    ).json()

    uris = []
    verified = []

    for t in tracks:
        if len(uris) >= target_count:
            break

        for q in [
            f"track:{t['song']} artist:{t['artist']}",
            t["song"],
            f"artist:{t['artist']}",
        ]:
            time.sleep(0.15)
            sp = search(headers, q)
            if not sp:
                continue

            if sp["artist"].lower() in banned:
                continue

            ok, match = verify(t, sp)
            if not ok:
                continue

            if sp["uri"] in uris:
                continue

            uris.append(sp["uri"])
            verified.append({"requested": t, "spotify": sp, "match_type": match})
            break

    if uris:
        requests.post(
            f"https://api.spotify.com/v1/playlists/{playlist['id']}/tracks",
            headers=headers,
            json={"uris": uris},
        )

    return {
        "url": f"https://open.spotify.com/playlist/{playlist['id']}",
        "added_count": len(uris),
        "verified_tracks": verified,
    }
