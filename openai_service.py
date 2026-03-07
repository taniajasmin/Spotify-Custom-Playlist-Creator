import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_playlist(context: dict) -> str:
    f = context["fingerprint"]
    num = context["num_songs"]

    prompt = f"""
You are a world-class DJ and playlist curator.
Return ONLY valid JSON.

TASK:
Invent a UNIQUE, CATCHY, and CREATIVE playlist title and generate exactly {num} tracks.

VIBE FINGERPRINT (STRICT OBEDIENCE REQUIRED):
- Primary Genre: {f['primary_genre']}
- Energy Level: {f['energy_level']}
- Eras/Decades: {', '.join(f['era_bias'])}
- Archetype Category: {f['archetype']}

CONSTRAINTS:
1. TITLE: Do NOT use the word "{f['archetype']}" in the title. Invent something fresh based on the genre and eras.
2. GENRE DOMINANCE: At least {f['genre_constraints']['target_percent']}% of tracks MUST be {f['primary_genre']}.
3. PROHIBITED DRIFT: Strictly avoid {f['genre_constraints']['prohibited_drift']} tracks.
4. DO NOT PLAY: {context['do_not_play']}

JSON FORMAT:
{{
  "title": "Your Invented Creative Title",
  "description": "One sentence describing the vibe",
  "tracks": [
    {{ "artist": "Artist Name", "song": "Song Title" }}
  ]
}}
"""

    r = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a specialized music curator who follows genre constraints perfectly."},
            {"role": "user", "content": prompt},
        ],
    )
    return r.choices[0].message.content