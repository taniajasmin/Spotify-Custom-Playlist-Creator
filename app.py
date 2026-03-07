from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List, Union
import json

from fastapi.concurrency import run_in_threadpool
from openai_service import generate_playlist
from spotify_service import create_playlist

app = FastAPI(title="AI Playlist Service")

class PlaylistRequest(BaseModel):
    answers: Dict[str, Union[str, List[str]]]
    user_type: str

def calculate_vibe_archetype(answers: dict) -> dict:
    # 1. Base Scores
    scores = {"E": 50, "M": 50, "G": 50, "L": 50, "N": 50}

    def add(d):
        for k, v in d.items():
            scores[k] += v

    # Q1: Event context
    q1 = answers.get("q1", "")
    if "Wedding (Evening" in q1: add({"E": 15, "N": 10})
    elif "Wedding (Drinks" in q1: add({"E": -20, "L": 15})
    elif "Corporate" in q1: add({"M": 10, "G": 10})

    # Q2: Energy (Updated per Spec V2.1)
    q2 = answers.get("q2", "")
    if "High-energy" in q2: add({"E": 25, "G": 5})
    elif "Medium" in q2 or "Elegant" in q2: add({"E": 15})
    elif "Low" in q2: add({"E": 5, "G": -2})

    # Q7: Decades (Era Bias)
    selected_decades = answers.get("q7", [])
    decade_map = {"70s": 20, "80s": 20, "90s": 15, "00s": 10}
    for d in selected_decades:
        for key, score in decade_map.items():
            if key in d: add({"N": score})

    # Q8: Genre Pick (DOMINANT DRIVER per Spec V2.1)
    primary_genre = "GENERAL"
    genres = answers.get("q8", [])
    for g in genres:
        if "Indie" in g:
            add({"G": -30, "N": 10, "E": 5})
            primary_genre = "INDIE_ALT"
        elif "House" in g:
            add({"G": 30, "E": 10, "M": 10})
            primary_genre = "HOUSE_DANCE"
        elif "Disco" in g or "Funk" in g:
            add({"G": -10, "N": 20, "E": 5})
            primary_genre = "DISCO_FUNK"
        elif "Pop" in g or "Chart" in g:
            add({"M": 20, "G": 5, "E": 5})
            primary_genre = "POP_CHART"

    # Clip scores 0-100
    for k in scores:
        scores[k] = max(0, min(100, scores[k]))

    E, M, G, L, N = scores.values()

    # 2. Archetype Selection (Thresholds)
    archetype = "CUSTOM"
    if G >= 65 and E >= 60: archetype = "IBIZA_AFTERGLOW"
    elif E <= 40 and L >= 55: archetype = "CHAMPAGNE_SUNSET"
    elif N >= 65 and E >= 45: archetype = "GOLDEN_NOSTALGIA"
    elif M >= 65 and E >= 50: archetype = "MODERN_LUXE"
    elif G <= 35 and N >= 40: archetype = "INDIE_DISCO"
    
    # 3. Create the Vibe Fingerprint (DNA for OpenAI)
    fingerprint = {
        "archetype": archetype,
        "primary_genre": primary_genre,
        "energy_level": "HIGH" if E > 70 else "MEDIUM" if E > 40 else "LOW",
        "era_bias": selected_decades,
        "genre_constraints": {
            "target_percent": 75 if primary_genre != "GENERAL" else 40,
            "prohibited_drift": "EDM/House" if primary_genre == "INDIE_ALT" else "Indie"
        }
    }

    return fingerprint

@app.post("/generate-playlist")
async def generate_playlist_api(payload: PlaylistRequest):
    target_count = 15 if payload.user_type.lower() == "free" else 50
    
    # Calculate Fingerprint instead of just a label
    fingerprint = calculate_vibe_archetype(payload.answers)

    # Merge Q10 + Q11 Banned Artists
    banned = []
    q10 = payload.answers.get("q10", "")
    if isinstance(q10, str) and q10.strip(): banned.append(q10.strip())
    q11 = payload.answers.get("q11", [])
    if isinstance(q11, list): banned.extend([str(x).strip() for x in q11 if x])

    # AI Generation with Fingerprint
    ai_json = await run_in_threadpool(
        generate_playlist,
        {
            "fingerprint": fingerprint,
            "do_not_play": ", ".join(banned),
            "num_songs": 25 if payload.user_type.lower() == "free" else 65,
        }
    )

    try:
        data = json.loads(ai_json)
    except Exception:
        return {"success": False, "error": "AI Response Error"}

    # Spotify Creation
    result = await run_in_threadpool(
        create_playlist,
        data["title"],
        data["description"],
        data["tracks"],
        banned,
        target_count,
    )

    return {
        "success": True,
        "playlist": {
            "title": data["title"],
            "description": data["description"],
            "vibe_archetype": fingerprint["archetype"],
            "spotify_url": result["url"],
            "tracks": [{"artist": t["spotify"]["artist"], "song": t["spotify"]["song"]} for t in result["verified_tracks"]]
        }
    }

@app.get("/")
def health(): return {"status": "ok"}