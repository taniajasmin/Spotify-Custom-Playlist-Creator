import os
import base64
import time
import re
import requests
import unicodedata
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


def normalize(text):
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]", "", text.lower())


def search(headers, q):
    for _ in range(3):
        r = requests.get(
            "https://api.spotify.com/v1/search",
            headers=headers,
            params={"q": q, "type": "track", "limit": 1},
            timeout=10,
        )

        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 1))
            time.sleep(wait)
            continue

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
            "all_artists": [a["name"] for a in t["artists"]],
        }

    return None


def is_banned(sp, banned):
    banned_norm = [normalize(b) for b in banned]

    for artist in sp.get("all_artists", []):
        norm_artist = normalize(artist)
        for b in banned_norm:
            if b in norm_artist:
                return True
    return False


def verify(req, sp, banned):
    if normalize(req["artist"]) == normalize(sp["artist"]) and normalize(req["song"]) == normalize(sp["song"]):
        return True, "exact"

    if normalize(req["artist"]) == normalize(sp["artist"]):
        return True, "title_variant"

    # Disable loose matching when banned list exists
    if not banned:
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
            sp = search(headers, q)
            if not sp:
                continue

            ok, match = verify(t, sp, banned)
            if not ok:
                continue

            if is_banned(sp, banned):
                continue

            if sp["uri"] in uris:
                continue

            uris.append(sp["uri"])
            verified.append({
                "requested": t,
                "spotify": sp,
                "match_type": match
            })
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
