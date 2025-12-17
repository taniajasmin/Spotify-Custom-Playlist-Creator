# AI Playlist Generator – FastAPI Microservice

This service is an AI-powered playlist generator designed to work as a backend microservice.
It receives quiz answers and user type from your main backend, calculates the event vibe, generates a curated playlist using OpenAI, and creates a real Spotify playlist.

## Key Features

- Business-rule enforced
  - Free users → 15 songs
  - Paid users → 50 songs

- Advanced vibe scoring engine
- Playlist generation via OpenAI
- Real playlist creation via Spotify Web API
- Backend-controlled (frontend cannot cheat)
- Clean JSON API (no HTML, no forms)

## Architecture Overview
```text
Frontend
↓ (Form data)
Your Main Backend
↓ (JSON: answers + user_type)
AI Playlist Service (this repo)
↓
OpenAI + Spotify API
```
Notes:

- text- Frontend never talks to this service directly
- Your backend decides whether the user is free or paid
- This AI service enforces the song limits

## Project Structure
```text
.
├── main.py                 # FastAPI application
├── openai_service.py       # OpenAI playlist generation logic
├── spotify_service.py      # Spotify auth & playlist creation
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.10+
- Spotify Developer Account (with an app created)
- OpenAI API Key

## Installation

1. Create a virtual environment

```Bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
# or
venv\Scripts\activate           # Windows
```

2. Install dependencies

```Bash
pip install -r requirements.txt
```

3. Environment Variables
Create a .env file in the root directory:
```env
OPENAI_API_KEY=your_openai_api_key

SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REFRESH_TOKEN=your_spotify_refresh_token
Note: The refresh token should belong to a Spotify account that will own the created playlists.
```

4. Running the Server
```Bash
uvicorn main:app --reload --port 8000
```
The server will be available at:
```
http://localhost:8000
```
Interactive API docs (Swagger UI):
```
http://localhost:8000/docs
```

## API Endpoint
### POST /generate-playlist
Generates a playlist based on quiz answers and user type.
Request Body (JSON)
```JSON{
  "answers": {
    "q1": "Wedding Evening",
    "q2": "High-energy",
    "q3": "Espresso martinis",
    "q4": "26–35",
    "q5": "Dua Lipa – Levitating",
    "q6": "Nice as an add-on",
    "q7": ["80s", "90s"],
    "q8": ["Pop/Disco/Dance Classics", "Chart/Top 40 only"],
    "q9": "Up and bouncing",
    "q10": "No Ed Sheeran"
  },
  "user_type": "free"
}
```

#### user_type options:

| Value | Result    |
|-------|-----------|
| free  | 15 songs  |
| paid  | 50 songs  |

Response (JSON)
```JSON{
  "success": true,
  "playlist": {
    "title": "Ibiza Afterglow",
    "description": "An energetic house-driven playlist with euphoric drops and vocal anthems...",
    "vibe": "Ibiza Afterglow",
    "song_count": 15,
    "spotify_url": "https://open.spotify.com/playlist/xxxxxx",
    "tracks": [
      { "artist": "Calvin Harris", "song": "I'm Not Alone" },
      { "artist": "Dua Lipa", "song": "Don't Start Now" }
    ]
  },
  "vibe_details": {
    "scores": {
      "E": 100,
      "M": 95,
      "G": 85,
      "L": 65,
      "N": 90
    },
    "keywords": "piano house, euphoric, vocal house"
  }
}
```

## Vibe Engine
The service computes scores for five dimensions:

- E – Energy
- M – Modern
- G – Groove
- L – Live / Luxe
- N – Nostalgia

These scores are combined to determine a vibe archetype, e.g.:

- Ibiza Afterglow
- Golden Nostalgia
- Modern Luxe
- Champagne Sunset

Security & Design Notes

- Frontend cannot choose song count or bypass limits
- Your backend decides the user_type
- This service strictly enforces song limits
- Designed for horizontal scaling (stateless)
- Safe to run multiple replicas behind a load balancer
