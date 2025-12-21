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


# VIBE LOGIC
def calculate_vibe_archetype(answers: dict) -> dict:
    scores = {"E": 50, "M": 50, "G": 50, "L": 50, "N": 50}

    def add(v):
        for k, x in v.items():
            scores[k] += x

    if "High-energy" in answers.get("q2", ""):
        add({"E": 30, "G": 15})

    if "80" in " ".join(answers.get("q7", [])):
        add({"N": 20})

    for k in scores:
        scores[k] = max(0, min(100, scores[k]))

    vibe_name = "Ibiza Afterglow" if scores["G"] >= 65 else "Custom Party Vibe"

    return {
        "scores": scores,
        "vibe_name": vibe_name,
        "keywords": "piano house, euphoric, vocal house",
        "do_not_play": answers.get("q10", "")
    }


@app.post("/generate-playlist")
async def generate_playlist_api(payload: PlaylistRequest):

    user_type = payload.user_type.lower()

    if user_type == "free":
        target_count = 15
        gpt_count = 25
    elif user_type == "paid":
        target_count = 50
        gpt_count = 65
    else:
        return {"success": False, "error": "Invalid user_type"}

    vibe = calculate_vibe_archetype(payload.answers)

    # GPT
    ai_json = await run_in_threadpool(
        generate_playlist,
        {
            "event": payload.answers.get("q1", ""),
            "vibe_name": vibe["vibe_name"],
            "keywords": vibe["keywords"],
            "vibe_scores": vibe["scores"],
            "do_not_play": vibe["do_not_play"],
            "num_songs": gpt_count,
        }
    )

    try:
        data = json.loads(ai_json)
    except Exception:
        return {"success": False, "error": "Invalid JSON from AI", "raw": ai_json}

    candidates = data.get("tracks", [])

    banned = [
        a.strip().lower()
        for a in payload.answers.get("q10", "").replace("No ", "").split(",")
        if a.strip()
    ]

    # SPOTIFY
    result = await run_in_threadpool(
        create_playlist,
        data["title"],
        data["description"],
        candidates,
        banned,
        target_count,
    )

    verified = result["verified_tracks"]

    return {
        "success": True,
        "playlist": {
            "title": data["title"],
            "description": data["description"],
            "vibe": vibe["vibe_name"],
            "requested_song_count": target_count,
            "spotify_song_count": result["added_count"],
            "spotify_url": result["url"],

            "tracks": [
                {
                    "artist": t["spotify"]["artist"],
                    "song": t["spotify"]["song"],
                    "match_type": t["match_type"]
                }
                for t in verified
            ]
        },
        "verification": {
            "exact": sum(1 for t in verified if t["match_type"] == "exact"),
            "variants": sum(1 for t in verified if t["match_type"] == "title_variant"),
            "fallbacks": sum(1 for t in verified if t["match_type"] == "track_only"),
        }
}

@app.get("/")
def health():
    return {"status": "ok"}
