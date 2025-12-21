import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_playlist(context: dict) -> str:
    num = context["num_songs"]

    prompt = f"""
You are the world's best professional event playlist curator.
Return ONLY valid JSON.

Generate EXACTLY {num} tracks.

Vibe: {context['vibe_name']}
Keywords: {context['keywords']}
Do not include: {context['do_not_play']}

Format:
{{
  "title": "Playlist title",
  "description": "One sentence",
  "tracks": [
    {{ "artist": "Artist", "song": "Song" }}
  ]
}}
"""

    r = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "Strict JSON only"},
            {"role": "user", "content": prompt},
        ],
    )

    return r.choices[0].message.content
