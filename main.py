# from fastapi import FastAPI, Request, Form
# from fastapi.responses import HTMLResponse, JSONResponse
# from fastapi.templating import Jinja2Templates
# from fastapi.staticfiles import StaticFiles
# import json

# from openai_service import generate_playlist
# from spotify_service import create_playlist

# app = FastAPI()
# app.mount("/static", StaticFiles(directory="."), name="static")
# templates = Jinja2Templates(directory=".")


# # =========================
# # VIBE SCORING & ARCHETYPE ENGINE
# # =========================
# def calculate_vibe_archetype(answers: dict) -> dict:
#     # Initialize scores
#     scores = {"E": 50, "M": 50, "G": 50, "L": 50, "N": 50}  # Start neutral

#     # Helper to add points
#     def add(points: dict):
#         for k, v in points.items():
#             scores[k] += v

#     # Q1 - Event type
#     q1 = answers.get("q1", "")
#     if "Wedding (Evening party)" in q1:
#         add({"E": 15, "N": 10})
#     elif "Wedding (Drinks reception)" in q1:
#         add({"E": -20, "L": 15})
#     elif "Corporate" in q1:
#         add({"M": 10, "G": 10})
#     elif "Private party" in q1 or "milestone" in q1:
#         add({"E": 10, "N": 5})
#     elif "Black-tie" in q1:
#         add({"E": -10, "M": -5, "L": 10})

#     # Q2 - Overall vibe
#     q2 = answers.get("q2", "")
#     if "Elegant & modern" in q2:
#         add({"E": -5, "M": 15, "G": 5, "L": 10})
#     elif "Fun & nostalgic" in q2:
#         add({"N": 25, "E": 5})
#     elif "High-energy floorfillers" in q2:
#         add({"E": 30, "G": 15})
#     elif "Ibiza sunset" in q2:
#         add({"E": 15, "G": 30, "M": 10})
#     elif "Indie/cool" in q2:
#         add({"G": -10, "N": 10})

#     # Q3 - Drinks moment
#     q3 = answers.get("q3", "")
#     if "Champagne" in q3:
#         add({"L": 10, "M": 5, "E": -5})
#     elif "Espresso martinis" in q3:
#         add({"E": 10, "M": 10})
#     elif "Craft cocktails" in q3:
#         add({"M": 15, "G": 5})
#     elif "Pints" in q3:
#         add({"N": 15})
#     elif "Rosé" in q3:
#         add({"G": 10})

#     # Q4 - Crowd age
#     q4 = answers.get("q4", "")
#     if "18–25" in q4:
#         add({"M": 25, "E": 10})
#     elif "26–35" in q4:
#         add({"M": 10, "E": 5})
#     elif "36–45" in q4:
#         add({"N": 10})
#     elif "46–60" in q4:
#         add({"N": 20})
#     elif "Mixed" in q4:
#         add({"N": 10, "E": 5})

#     # Q5 - Floorfiller
#     q5 = answers.get("q5", "")
#     if "ABBA" in q5:
#         add({"N": 20, "G": 10})
#     elif "Calvin Harris" in q5:
#         add({"E": 10, "G": 15, "M": 10})
#     elif "Dua Lipa" in q5:
#         add({"M": 15, "G": 10})
#     elif "Queen" in q5:
#         add({"N": 20, "E": 10})
#     elif "Fleetwood Mac" in q5:
#         add({"N": 25})

#     # Q6 - Sax
#     q6 = answers.get("q6", "")
#     if "Absolutely" in q6:
#         add({"L": 30})
#     elif "Nice as an add-on" in q6:
#         add({"L": 15})

#     # Q7 - Decades (multiple)
#     q7 = answers.get("q7", [])
#     for decade in q7:
#         if "70s" in decade: add({"N": 20})
#         if "80s" in decade: add({"N": 20})
#         if "90s" in decade: add({"N": 15})
#         if "00s" in decade: add({"N": 10})
#         if "10s" in decade or "Now" in decade: add({"M": 20})

#     # Q8 - Genre lean (up to 2)
#     q8 = answers.get("q8", [])
#     for genre in q8:
#         if "Pop/Disco" in genre:
#             add({"G": 5, "N": 10})
#         elif "House/Euphoric" in genre:
#             add({"G": 30, "M": 10})
#         elif "R&B" in genre:
#             add({"N": 15, "E": 10})
#         elif "Indie/Alt" in genre:
#             add({"G": -5, "N": 10})
#         elif "Chart" in genre:
#             add({"M": 25, "G": 10})

#     # Q9 - Last hour energy
#     q9 = answers.get("q9", "")
#     if "Smooth & chic" in q9:
#         add({"E": -15})
#     elif "Up and bouncing" in q9:
#         add({"E": 15})
#     elif "Lose our minds" in q9:
#         add({"E": 30})

#     # Clip to 0–100
#     for k in scores:
#         scores[k] = max(0, min(100, scores[k]))

#     E, M, G, L, N = scores.values()

#     # =========================
#     # ARCHETYPE DETECTION (top-to-bottom)
#     # =========================
#     archetype = "CUSTOM_VIBE"
#     vibe_name = "Your Perfect Party Vibe"
#     keywords = ""

#     if G >= 65 and E >= 60 and M >= 50:
#         archetype = "IBIZA_AFTERGLOW"
#         vibe_name = "Ibiza Afterglow"
#         keywords = "piano house, vocal house, euphoric, sunset vibes, Balearic, Anjuna"
#     elif E <= 40 and L >= 55 and 35 <= M <= 70:
#         archetype = "CHAMPAGNE_SUNSET"
#         vibe_name = "Champagne Sunset"
#         keywords = "nu-disco, French house, silky pop, live instruments, sax solos, elegant"
#     elif N >= 60 and E >= 45:
#         archetype = "GOLDEN_NOSTALGIA"
#         vibe_name = "Golden Nostalgia Floorfillers"
#         keywords = "70s 80s 90s 00s, singalongs, ABBA, Queen, family dancefloor"
#     elif M >= 65 and 45 <= E <= 80:
#         archetype = "MODERN_LUXE"
#         vibe_name = "Modern Luxe Party"
#         keywords = "current chart, sleek edits, Dua Lipa, Calvin Harris, high production"
#     elif G <= 30 and N >= 35:
#         archetype = "INDIE_DISCO"
#         vibe_name = "Indie Disco Lights"
#         keywords = "indie dance, Arctic Monkeys, Two Door, bloghaus, guitars"
#     elif E <= 30 and 35 <= N <= 70:
#         archetype = "CLASSIC_CHIC"
#         vibe_name = "Classic Chic Reception"
#         keywords = "Motown, soul classics, cocktail hour, timeless elegance"

#     return {
#         "scores": scores,
#         "archetype": archetype,
#         "vibe_name": vibe_name,
#         "keywords": keywords,
#         "do_not_play": answers.get("q10", "").strip()
#     }


# @app.get("/", response_class=HTMLResponse)
# async def home(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request})


# # @app.post("/quiz/submit")
# # async def submit_quiz(
# #     q1: str = Form(...),
# #     q2: str = Form(...),
# #     q3: str = Form(...),
# #     q4: str = Form(...),
# #     q5: str = Form(...),
# #     q6: str = Form(...),
# #     q7: list[str] = Form([]),
# #     q8: list[str] = Form([]),
# #     q9: str = Form(...),
# #     q10: str = Form(""),
# #     song_count: str = Form("15"),  
# # ):
# #     answers = {
# #         "q1": q1, "q2": q2, "q3": q3, "q4": q4, "q5": q5,
# #         "q6": q6, "q7": q7, "q8": q8, "q9": q9, "q10": q10
# #     }

# #     vibe = calculate_vibe_archetype(answers)
# #     num_songs = 50 if song_count == "50" else 15

# #     print("Final vibe:", vibe)
# #     print(f"Generating {num_songs} songs")

# #     ai_response = generate_playlist({
# #         "user_answers": answers,
# #         "vibe_scores": vibe["scores"],
# #         "archetype": vibe["archetype"],
# #         "vibe_name": vibe["vibe_name"],
# #         "keywords": vibe["keywords"],
# #         "do_not_play": vibe["do_not_play"],
# #         "event": q1,
# #         "num_songs": num_songs
# #     })

# #     try:
# #         data = json.loads(ai_response)
# #     except json.JSONDecodeError as e:
# #         return JSONResponse({"error": "AI returned invalid JSON", "raw": ai_response}, status_code=500)

# #     try:
# #         spotify_url = create_playlist(data["title"], data["description"], data["tracks"])
# #     except Exception as e:
# #         return JSONResponse({"error": "Spotify failed", "details": str(e)}, status_code=500)

# #     # FINAL CLEAN JSON OUTPUT
# #     return JSONResponse({
# #         "success": True,
# #         "playlist": {
# #             "title": data["title"],
# #             "description": data["description"],
# #             "vibe": vibe["vibe_name"],
# #             "song_count": len(data["tracks"]),
# #             "spotify_url": spotify_url,
# #             "tracks": data["tracks"]  # full track list for embedding
# #         },
# #         "debug": {
# #             "scores": vibe["scores"],
# #             "archetype": vibe["archetype"]
# #         }
# #     })

# @app.post("/quiz/submit")
# async def submit_quiz(
#     q1: str = Form(...),
#     q2: str = Form(...),
#     q3: str = Form(...),
#     q4: str = Form(...),
#     q5: str = Form(...),
#     q6: str = Form(...),
#     q7: list[str] = Form([]),
#     q8: list[str] = Form([]),
#     q9: str = Form(...),
#     q10: str = Form(""),
#     song_count: str = Form("15"),
# ):
#     answers = {f"q{i}": v for i, v in locals().items() if f"q{i}" in str(v)}
#     answers["q7"] = q7
#     answers["q8"] = q8

#     vibe = calculate_vibe_archetype(answers)
#     num_songs = 50 if song_count == "50" else 15

#     ai_json = generate_playlist({
#         "event": q1,
#         "vibe_name": vibe["vibe_name"],
#         "keywords": vibe["keywords"],
#         "vibe_scores": vibe["scores"],
#         "do_not_play": q10.strip() or "none",
#         "num_songs": num_songs
#     })

#     try:
#         data = json.loads(ai_json)
#     except Exception as e:
#         return JSONResponse({"error": "Invalid JSON from AI", "raw": ai_json}, status_code=500)

#     # ENFORCE exact number of songs
#     if "tracks" not in data or len(data["tracks"]) != num_songs:
#         # Fallback: pad or trim to correct length
#         if len(data.get("tracks", [])) < num_songs:
#             data["tracks"] = (data.get("tracks", []) + [{"artist": "Various Artists", "song": "Bonus Track"}])[:num_songs]
#         else:
#             data["tracks"] = data["tracks"][:num_songs]

#     spotify_url = create_playlist(data["title"], data["description"], data["tracks"])

#     # FINAL CLEAN JSON (this is what you wanted)
#     return JSONResponse({
#         "success": True,
#         "playlist": {
#             "title": data["title"],
#             "description": data["description"],
#             "vibe": vibe["vibe_name"],
#             "song_count": len(data["tracks"]),
#             "requested_songs": num_songs,
#             "spotify_url": spotify_url,
#             "tracks": data["tracks"]
#         },
#         "vibe_details": {
#             "archetype": vibe["archetype"],
#             "scores": vibe["scores"],
#             "keywords": vibe["keywords"]
#         }
#     })


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


# =========================
# VIBE SCORING ENGINE
# =========================
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
