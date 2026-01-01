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

# VIBE ENGINE
def calculate_vibe_archetype(answers: dict) -> dict:
    scores = {"E": 50, "M": 50, "G": 50, "L": 50, "N": 50}

    def add(d):
        for k, v in d.items():
            scores[k] += v

    # Q1 — EVENT TYPE
    q1 = answers.get("q1", "")
    if "Wedding (Evening" in q1:
        add({"E": 15, "N": 10})
    elif "Wedding (Drinks" in q1:
        add({"E": -20, "L": 15})
    elif "Corporate" in q1:
        add({"M": 10, "G": 10})
    elif "Private" in q1:
        add({"E": 10, "N": 5})
    elif "Black-tie" in q1:
        add({"E": -10, "M": -5, "L": 10})

    # Q2 — OVERALL VIBE
    q2 = answers.get("q2", "")
    if "Elegant" in q2:
        add({"E": -5, "M": 15, "G": 5, "L": 10})
    elif "Fun & nostalgic" in q2:
        add({"N": 25, "E": 5})
    elif "High-energy" in q2:
        add({"E": 30, "G": 15})
    elif "Ibiza" in q2:
        add({"E": 15, "G": 30, "M": 10})
    elif "Indie" in q2:
        add({"G": -10, "N": 10})

    # Q3 — DRINKS MOMENT
    q3 = answers.get("q3", "")
    if "Champagne" in q3:
        add({"L": 10, "M": 5, "E": -5})
    elif "Espresso" in q3:
        add({"E": 10, "M": 10})
    elif "Craft" in q3:
        add({"M": 15, "G": 5})
    elif "Pints" in q3:
        add({"N": 15})
    elif "Rosé" in q3:
        add({"G": 10})

    # Q4 — AGE RANGE
    q4 = answers.get("q4", "")
    if "18–25" in q4:
        add({"M": 25, "E": 10})
    elif "26–35" in q4:
        add({"M": 10, "E": 5})
    elif "36–45" in q4:
        add({"N": 10})
    elif "46–60" in q4:
        add({"N": 20})
    else:
        add({"N": 10, "E": 5})

    # Q5 — FLOORFILLER
    q5 = answers.get("q5", "")
    if "ABBA" in q5:
        add({"N": 20, "G": 10})
    elif "Calvin" in q5:
        add({"E": 10, "G": 15, "M": 10})
    elif "Dua" in q5:
        add({"M": 15, "G": 10})
    elif "Queen" in q5:
        add({"N": 20, "E": 10})
    elif "Fleetwood" in q5:
        add({"N": 25})

    # Q6 — SAX
    q6 = answers.get("q6", "")
    if "Absolutely" in q6:
        add({"L": 30})
    elif "Nice" in q6:
        add({"L": 15})

    # Q7 — DECADES (TRACK EXPLICITLY)
    selected_decades = answers.get("q7", [])
    decade_labels = []
    decade_map = {"70s": 20, "80s": 20, "90s": 15, "00s": 10}

    for d in selected_decades:
        for key, score in decade_map.items():
            if key in d:
                add({"N": score})
                decade_labels.append(key)

    # Q8 — GENRE LEAN
    for g in answers.get("q8", []):
        if "Pop" in g:
            add({"G": 5, "N": 10})
        elif "House" in g:
            add({"G": 30, "M": 10})
        elif "R&B" in g:
            add({"N": 15, "E": 10})
        elif "Indie" in g:
            add({"G": -5, "N": 10})
        elif "Chart" in g:
            add({"M": 25, "G": 10})

    # Q9 — LAST HOUR
    q9 = answers.get("q9", "")
    if "Smooth" in q9:
        add({"E": -15})
    elif "Up and bouncing" in q9:
        add({"E": 15})
    elif "Lose" in q9:
        add({"E": 30})

    # NORMALISE
    for k in scores:
        scores[k] = max(0, min(100, scores[k]))

    E, M, G, L, N = scores.values()

    # ARCHETYPES
    archetype = "CUSTOM"
    title = "Custom Party Vibe"

    if G >= 65 and E >= 60 and M >= 50:
        archetype = "IBIZA_AFTERGLOW"
        title = "Ibiza Afterglow Set"
    elif E <= 40 and L >= 55 and 35 <= M <= 70:
        archetype = "CHAMPAGNE_SUNSET"
        title = "Champagne Sunset Mix"
    elif N >= 60 and E >= 45:
        archetype = "GOLDEN_NOSTALGIA"
        title = "Golden Nostalgia Floorfillers"
    elif M >= 65 and 45 <= E <= 80:
        archetype = "MODERN_LUXE"
        title = "Modern Luxe Party Set"
    elif G <= 30 and N >= 35:
        archetype = "INDIE_DISCO"
        title = "Indie Disco Lights"
    elif E <= 30 and 35 <= N <= 70:
        archetype = "CLASSIC_CHIC"
        title = "Classic Chic Reception"

    keywords = f"{', '.join(decade_labels)} singalongs" if decade_labels else "party favourites"

    return {
        "scores": scores,
        "archetype": archetype,
        "vibe_name": title,
        "keywords": keywords,
        "do_not_play": answers.get("q10", "")
    }

# API ENDPOINT 
@app.post("/generate-playlist")
async def generate_playlist_api(payload: PlaylistRequest):

    target_count = 15 if payload.user_type.lower() == "free" else 50
    gpt_count = 25 if payload.user_type.lower() == "free" else 65

    vibe = calculate_vibe_archetype(payload.answers)

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

        # validate required structure
        if not all(k in data for k in ("title", "description", "tracks")):
            raise ValueError("Missing required keys")

        if not isinstance(data["tracks"], list):
            raise ValueError("Tracks must be a list")

    except Exception:
        return {
            "success": False,
            "error": "Invalid AI response",
            "raw": ai_json,
        }


    raw = payload.answers.get("q10", "").lower()
    for p in ["no ", "do not play", "don't play"]:
        raw = raw.replace(p, "")
    banned = [x.strip() for x in raw.split(",") if x.strip()]

    result = await run_in_threadpool(
        create_playlist,
        data["title"],
        data["description"],
        data["tracks"],
        banned,
        target_count,
    )

    # return {
    #     "success": True,
    #     "playlist": {
    #         "title": data["title"],
    #         "description": data["description"],
    #         "vibe": vibe["vibe_name"],
    #         "spotify_song_count": result["added_count"],
    #         "spotify_url": result["url"],
    #     },

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
                    "match_type": t["match_type"],
                }
                for t in verified
            ],
        },
        "verification": {
            "exact": sum(1 for t in verified if t["match_type"] == "exact"),
            "variants": sum(1 for t in verified if t["match_type"] == "title_variant"),
            "fallbacks": sum(1 for t in verified if t["match_type"] == "track_only"),
        },
    }

@app.get("/")
def health():
    return {"status": "ok"}
