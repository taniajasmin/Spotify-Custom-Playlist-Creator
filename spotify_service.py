import os, base64, time, re, requests, unicodedata
from dotenv import load_dotenv

load_dotenv()
CID = os.getenv("SPOTIFY_CLIENT_ID")
CS = os.getenv("SPOTIFY_CLIENT_SECRET")
RT = os.getenv("SPOTIFY_REFRESH_TOKEN")

def get_token():
    auth = base64.b64encode(f"{CID}:{CS}".encode()).decode()
    r = requests.post("https://accounts.spotify.com/api/token", 
                      data={"grant_type": "refresh_token", "refresh_token": RT},
                      headers={"Authorization": f"Basic {auth}"})
    return r.json()["access_token"]

def normalize(text):
    text = unicodedata.normalize("NFKD", str(text))
    return re.sub(r"[^a-z0-9]", "", text.lower())

def search(headers, q):
    r = requests.get("https://api.spotify.com/v1/search", headers=headers, 
                     params={"q": q, "type": "track", "limit": 1})
    if r.status_code != 200: return None
    items = r.json().get("tracks", {}).get("items", [])
    if not items: return None
    t = items[0]
    return {"uri": t["uri"], "song": t["name"], "artist": t["artists"][0]["name"], "all_artists": [a["name"] for a in t["artists"]]}

def is_banned(sp_artists, banned_list):
    """Whole-word matching to avoid banning 'Radiohead' if user bans 'Ed'"""
    for artist in sp_artists:
        norm_artist = normalize(artist)
        for b in banned_list:
            norm_b = normalize(b)
            # Check if banned word exists as a standalone word or full match
            if norm_b == norm_artist or re.search(rf"\b{re.escape(norm_b)}\b", norm_artist):
                return True
    return False

def verify(req, sp):
    req_art, req_sng = normalize(req["artist"]), normalize(req["song"])
    sp_art, sp_sng = normalize(sp["artist"]), normalize(sp["song"])
    
    if req_art == sp_art and req_sng == sp_sng: return True, "exact"
    # Title variant: Artist matches AND song title is contained within result
    if req_art == sp_art and (req_sng in sp_sng or sp_sng in req_sng): return True, "title_variant"
    return False, "reject"

def create_playlist(title, description, tracks, banned, target_count):
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    user = requests.get("https://api.spotify.com/v1/me", headers=headers).json()

    playlist = requests.post(f"https://api.spotify.com/v1/users/{user['id']}/playlists",
                             headers=headers, json={"name": title, "description": description, "public": False}).json()

    uris, verified = [], []
    for t in tracks:
        if len(uris) >= target_count: break
        
        # Try specific search
        sp = search(headers, f"track:{t['song']} artist:{t['artist']}")
        if not sp: sp = search(headers, f"{t['song']} {t['artist']}")
        
        if sp:
            ok, match = verify(t, sp)
            if ok and not is_banned(sp["all_artists"], banned):
                if sp["uri"] not in uris:
                    uris.append(sp["uri"])
                    verified.append({"requested": t, "spotify": sp, "match_type": match})
        time.sleep(0.1) # Prevent rate limiting

    if uris:
        requests.post(f"https://api.spotify.com/v1/playlists/{playlist['id']}/tracks", headers=headers, json={"uris": uris})

    return {"url": f"https://open.spotify.com/playlist/{playlist['id']}", "added_count": len(uris), "verified_tracks": verified}