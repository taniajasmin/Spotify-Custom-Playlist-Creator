from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json

from openai_service import generate_playlist
from spotify_service import create_playlist

app = FastAPI()
app.mount("/static", StaticFiles(directory="."), name="static")
templates = Jinja2Templates(directory=".")

# VIBE SCORING ENGINE
def calculate_vibe_archetype(answers: dict) -> dict:
    scores = {"E": 50, "M": 50, "G": 50, "L": 50, "N": 50}

    def add(values: dict):
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

    # Q7
    for decade in answers["q7"]:
        if "70" in decade: add({"N": 20})
        if "80" in decade: add({"N": 20})
        if "90" in decade: add({"N": 15})
        if "00" in decade: add({"N": 10})
        if "10" in decade: add({"M": 20})

    # Q8
    for genre in answers["q8"]:
        if "Pop" in genre:
            add({"N": 10})
        elif "House" in genre:
            add({"G": 30, "M": 10})
        elif "R&B" in genre:
            add({"N": 15})
        elif "Indie" in genre:
            add({"N": 10})
        elif "Chart" in genre:
            add({"M": 25, "G": 10})

    # Q9
    q9 = answers["q9"]
    if "Smooth" in q9:
        add({"E": -15})
    elif "Up and bouncing" in q9:
        add({"E": 15})
    elif "Lose" in q9:
        add({"E": 30})

    # clamp scores
    for k in scores:
        scores[k] = max(0, min(100, scores[k]))

    # Detect vibe
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
        "do_not_play": answers["q10"].strip(),
    }


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/quiz/submit")
async def submit_quiz(
    q1: str = Form(...),
    q2: str = Form(...),
    q3: str = Form(...),
    q4: str = Form(...),
    q5: str = Form(...),
    q6: str = Form(...),
    q7: list[str] = Form([]),
    q8: list[str] = Form([]),
    q9: str = Form(...),
    q10: str = Form(""),
    song_count: str = Form("15"),
):

    # FIXED answers dictionary
    answers = {
        "q1": q1, "q2": q2, "q3": q3, "q4": q4,
        "q5": q5, "q6": q6, "q7": q7, "q8": q8,
        "q9": q9, "q10": q10
    }

    print("\n=== USER ANSWERS SUBMITTED ===")
    print(json.dumps(answers, indent=2))

    vibe = calculate_vibe_archetype(answers)

    num_songs = 50 if song_count == "50" else 15

    ai_json = generate_playlist({
        "event": q1,
        "vibe_name": vibe["vibe_name"],
        "keywords": vibe["keywords"],
        "vibe_scores": vibe["scores"],
        "do_not_play": q10.strip() or "none",
        "num_songs": num_songs,
    })

    try:
        data = json.loads(ai_json)

        print("\n JSON OUTPUT")
        print(json.dumps(data, indent=2))
        print("======================\n")

    except:
        return JSONResponse({"error": "AI returned invalid JSON", "raw": ai_json})

    # ENFORCE EXACT SONG COUNT
    tracks = data.get("tracks", [])

    if len(tracks) < num_songs:
        while len(tracks) < num_songs:
            tracks.append({"artist": "Various Artists", "song": f"Bonus Track {len(tracks)+1}"})

    if len(tracks) > num_songs:
        tracks = tracks[:num_songs]

    data["tracks"] = tracks

    url = create_playlist(data["title"], data["description"], tracks)

    final_response = {
        "success": True,
        "playlist": {
            "title": data["title"],
            "description": data["description"],
            "vibe": vibe["vibe_name"],
            "song_count": len(tracks),
            "spotify_url": url,
            "tracks": tracks,
        },
        "vibe_details": {
            "scores": vibe["scores"],
            "keywords": vibe["keywords"],
        }
    }

    print("\n=== FINAL JSON SENT TO FRONTEND ===")
    print(json.dumps(final_response, indent=2))
   
    return final_response
