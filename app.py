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
    # Base scores
    scores = {"E": 50, "M": 50, "G": 50, "L": 50, "N": 50}

    def add(v):
        for k, x in v.items():
            scores[k] += x

    # Q1: EVENT TYPE
    q1 = answers.get("q1", "")
    if "Wedding (Evening party)" in q1:
        add({"E": 15, "N": 10})
    elif "Wedding (Drinks reception)" in q1:
        add({"E": -20, "L": 15})
    elif "Corporate" in q1:
        add({"M": 10, "G": 10})
    elif "Private" in q1:
        add({"E": 10, "N": 5})
    elif "Black-tie" in q1:
        add({"E": -10, "M": -5, "L": 10})

    # Q2: OVERALL VIBE
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

    # Q3: DRINKS MOMENT
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

    # Q4: AGE RANGE
    q4 = answers.get("q4", "")
    if "18" in q4:
        add({"M": 25, "E": 10})
    elif "26" in q4:
        add({"M": 10, "E": 5})
    elif "36" in q4:
        add({"N": 10})
    elif "46" in q4:
        add({"N": 20})
    else:  # Mixed ages
        add({"N": 10, "E": 5})

    # Q5: FLOORFILLER
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

    # Q6: SAX
    q6 = answers.get("q6", "")
    if "Absolutely" in q6:
        add({"L": 30})
    elif "Nice" in q6:
        add({"L": 15})

    # Q7: DECADES (MULTI)
    for d in answers.get("q7", []):
        if "70" in d:
            add({"N": 20})
        if "80" in d:
            add({"N": 20})
        if "90" in d:
            add({"N": 15})
        if "00" in d:
            add({"N": 10})
        if "10" in d:
            add({"M": 20})

    # Q8: GENRE LEAN (MULTI)
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

    # Q9: LAST HOUR
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

    # ARCHETYPE RULES (ORDERED)
    E, M, G, L, N = scores["E"], scores["M"], scores["G"], scores["L"], scores["N"]

    archetype = "CUSTOM"
    title = "Custom Party Vibe"
    keywords = "party mix"

    if G >= 65 and E >= 60 and M >= 50:
        archetype = "IBIZA_AFTERGLOW"
        title = "Ibiza Afterglow Set"
        keywords = "house, vocal, piano, sunset"
    elif E <= 40 and L >= 55 and 35 <= M <= 70:
        archetype = "CHAMPAGNE_SUNSET"
        title = "Champagne Sunset Mix"
        keywords = "nu-disco, french touch, silky pop"
    elif N >= 60 and E >= 45:
        archetype = "GOLDEN_NOSTALGIA"
        title = "Golden Nostalgia Floorfillers"
        keywords = "70s–00s singalongs"
    elif M >= 65 and 45 <= E <= 80:
        archetype = "MODERN_LUXE"
        title = "Modern Luxe Party Set"
        keywords = "contemporary pop, sleek dance"
    elif G <= 30 and N >= 35:
        archetype = "INDIE_DISCO"
        title = "Indie Disco Lights"
        keywords = "indie dance, blog-era anthems"
    elif E <= 30 and 35 <= N <= 70:
        archetype = "CLASSIC_CHIC"
        title = "Classic Chic Reception"
        keywords = "motown, soul, cocktail classics"

    return {
        "scores": scores,
        "archetype": archetype,
        "vibe_name": title,
        "keywords": keywords,
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

    # banned = [
    #     a.strip().lower()
    #     for a in payload.answers.get("q10", "").replace("No ", "").split(",")
    #     if a.strip()
    # ]

    raw = payload.answers.get("q10", "")
    raw = raw.lower().replace("no ", "")
    banned = [x.strip() for x in raw.split(",") if x.strip()]

    result = await run_in_threadpool(
        create_playlist,
        data["title"],
        data["description"],
        candidates,
        banned,
        target_count,
    )


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
