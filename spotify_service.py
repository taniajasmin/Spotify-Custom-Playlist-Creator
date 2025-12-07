# spotify_service.py
import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN")


def get_access_token():
    auth_str = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    r = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "refresh_token", "refresh_token": REFRESH_TOKEN},
        headers={"Authorization": f"Basic {auth_str}"}
    )
    r.raise_for_status()
    return r.json()["access_token"]


def create_playlist(title: str, description: str, tracks: list[dict]):
    token = get_access_token()

    # Get user ID
    user_id = requests.get("https://api.spotify.com/v1/me", headers={"Authorization": f"Bearer {token}"}).json()["id"]

    # Create playlist
    pl = requests.post(
        f"https://api.spotify.com/v1/users/{user_id}/playlists",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"name": title, "description": description, "public": False}
    ).json()

    playlist_id = pl["id"]

    # Search & collect track URIs
    uris = []
    for track in tracks:
        q = f"track:{track['song']} artist:{track['artist']}"
        results = requests.get(
            "https://api.spotify.com/v1/search",
            params={"q": q, "type": "track", "limit": 1},
            headers={"Authorization": f"Bearer {token}"}
        ).json()

        if results["tracks"]["items"]:
            uris.append(results["tracks"]["items"][0]["uri"])

    # Add tracks
    if uris:
        requests.post(
            f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
            headers={"Authorization": f"Bearer {token}"},
            json={"uris": uris}
        )

    return f"https://open.spotify.com/playlist/{playlist_id}"