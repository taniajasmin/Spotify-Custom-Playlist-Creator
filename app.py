from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
import json

from openai_service import generate_playlist
from spotify_service import create_playlist

app = FastAPI(title="AI Playlist Service")


class QuizAnswers(BaseModel):
    answers: Dict[str, str | List[str]]


class PlaylistRequest(BaseModel):
    answers: Dict[str, str | List[str]]
    user_type: str          # "free" or "paid"
    song_count: int         # backend sets 15 or 50 (AI will enforce)

# STORE QUIZ ANSWERS from backend
@app.post("/quiz/answers")
async def receive_quiz_answers(payload: QuizAnswers):
    return {
        "success": True,
        "received_answers": payload.answers
    }

# VIBE SCORING ENGINE
def calculate_vibe_archetype(answers: dict) -> dict:
    scores = {"E": 50, "M": 50, "G": 50, "L": 50, "N": 50}

    def add(values):
        for k, v in values.items():
            scores[k] += v

    # Q1
    q1 = answers["q1"]
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

    # Q2
    q2 = answers["q2"]
    if "Elegant" in q2:
        add({"E": -5, "M": 15, "L": 10})
    elif "Fun & nostalgic" in q2:
        add({"N": 25, "E": 5})
    elif "High-energy" in q2:
        add({"E": 30, "G": 15})
    elif "Ibiza" in q2:
        add({"E": 15, "G": 30, "M": 10})
    elif "Indie" in q2:
        add({"N": 10, "G": -10})

    # Q3
    q3 = answers["q3"]
    if "Champagne" in q3:
        add({"L": 10, "M": 5})
    elif "Espresso" in q3:
        add({"E": 10, "M": 10})
    elif "Craft" in q3:
        add({"M": 15})
    elif "Pints" in q3:
        add({"N": 15})
    elif "Rosé" in q3:
        add({"G": 10})

    # Q4
    q4 = answers["q4"]
    if "18" in q4:
        add({"M": 25, "E": 10})
    elif "26" in q4:
        add({"M": 10, "E": 5})
    elif "36" in q4:
        add({"N": 10})
    elif "46" in q4:
        add({"N": 20})
    else:
        add({"N": 10, "E": 5})

    # Q5
    q5 = answers["q5"]
    if "ABBA" in q5:
        add({"N": 20, "G": 10})
    elif "Calvin" in q5:
        add({"M": 10, "G": 15})
    elif "Dua" in q5:
        add({"M": 15, "G": 10})
    elif "Queen" in q5:
        add({"N": 20, "E": 10})
    elif "Fleetwood" in q5:
        add({"N": 25})

    # Q6
    q6 = answers["q6"]
    if "Absolutely" in q6:
        add({"L": 30})
    elif "Nice" in q6:
        add({"L": 15})

    # Q7 list
    for d in answers["q7"]:
        if "70" in d: add({"N": 20})
        if "80" in d: add({"N": 20})
        if "90" in d: add({"N": 15})
        if "00" in d: add({"N": 10})
        if "10" in d: add({"M": 20})

    # Q8 list
    for g in answers["q8"]:
        if "Pop" in g:
            add({"N": 10})
        elif "House" in g:
            add({"G": 30, "M": 10})
        elif "R&B" in g:
            add({"N": 15})
        elif "Indie" in g:
            add({"N": 10})
        elif "Chart" in g:
            add({"M": 25, "G": 10})

    # Q9
    q9 = answers["q9"]
    if "Smooth" in q9:
        add({"E": -15})
    elif "Up and bouncing" in q9:
        add({"E": 15})
    elif "Lose" in q9:
        add({"E": 30})

    # clamp
    for k in scores:
        scores[k] = max(0, min(100, scores[k]))

    E, M, G, L, N = scores.values()

    vibe_name = "Custom Party Vibe"
    keywords = ""

    if G >= 65 and E >= 60:
        vibe_name = "Ibiza Afterglow"
        keywords = "piano house, euphoric, vocal house"
    elif N >= 60:
        vibe_name = "Golden Nostalgia"
        keywords = "70s 80s 90s singalongs, family dancefloor"
    elif M >= 65:
        vibe_name = "Modern Luxe"
        keywords = "sleek pop, Calvin Harris, Dua Lipa"
    elif L >= 55:
        vibe_name = "Champagne Sunset"
        keywords = "nu-disco, French house, chic"

    return {
        "scores": scores,
        "vibe_name": vibe_name,
        "keywords": keywords,
        "do_not_play": answers["q10"].strip()
    }


@app.post("/generate-playlist")
async def generate_playlist_api(payload: PlaylistRequest):

    answers = payload.answers
    user_type = payload.user_type
    num_songs = payload.song_count

    # Enforce allowed song count
    if user_type == "free":
        num_songs = 15
    elif user_type == "paid":
        num_songs = 50
    else:
        return {"success": False, "error": "Invalid user_type"}

    # Compute vibe
    vibe = calculate_vibe_archetype(answers)

    # Call OpenAI
    ai_json = generate_playlist({
        "event": answers["q1"],
        "vibe_name": vibe["vibe_name"],
        "keywords": vibe["keywords"],
        "vibe_scores": vibe["scores"],
        "do_not_play": vibe["do_not_play"],
        "num_songs": num_songs
    })

    # Parse JSON
    try:
        data = json.loads(ai_json)
    except:
        return {"success": False, "error": "Invalid JSON from AI", "raw": ai_json}

    # Enforce song count exactly
    tracks = data.get("tracks", [])
    if len(tracks) < num_songs:
        while len(tracks) < num_songs:
            tracks.append({
                "artist": "Various Artists",
                "song": f"Bonus Track {len(tracks)+1}"
            })
    if len(tracks) > num_songs:
        tracks = tracks[:num_songs]

    data["tracks"] = tracks

    # Create Spotify playlist
    url = create_playlist(data["title"], data["description"], tracks)

    # response
    return {
        "success": True,
        "playlist": {
            "title": data["title"],
            "description": data["description"],
            "vibe": vibe["vibe_name"],
            "song_count": len(tracks),
            "spotify_url": url,
            "tracks": tracks
        },
        "vibe_details": {
            "scores": vibe["scores"],
            "keywords": vibe["keywords"]
        }
    }
