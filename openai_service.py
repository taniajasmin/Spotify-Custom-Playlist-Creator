# import os
# import json
# from openai import OpenAI
# from dotenv import load_dotenv

# load_dotenv()
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# def generate_playlist(context: dict) -> str:
#     num = context.get("num_songs", 15)

#     prompt = f"""
# You are the world's best party playlist curator.

# Event: {context['event']}
# Vibe: {context['vibe_name']}
# Style: {context['keywords']}
# Energy {context['vibe_scores']['E']} | Modern {context['vibe_scores']['M']} | Nostalgia {context['vibe_scores']['N']}

# DO NOT include: {context['do_not_play'] or 'nothing'}

# Generate EXACTLY {num} tracks.
# Return ONLY valid JSON:

# {{
#   "title": "Amazing playlist title using the vibe name",
#   "description": "One beautiful sentence that sells the vibe",
#   "tracks": [
#     {{"artist": "Artist Name", "song": "Song Title"}},
#     ...
#   ]
# }}
# """

#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         response_format={"type": "json_object"},
#         temperature=0.8,
#         messages=[
#             {"role": "system", "content": "Return only valid JSON. No markdown, no explanations."},
#             {"role": "user", "content": prompt}
#         ]
#     )
#     return response.choices[0].message.content

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_playlist(context: dict) -> str:
    num = context.get("num_songs", 15)

    prompt = f"""
You are the world's best professional event playlist curator.

Event: {context['event']}
Vibe Name: {context['vibe_name']}
Keywords: {context['keywords']}
Energy {context['vibe_scores']['E']} | Modern {context['vibe_scores']['M']} | Nostalgia {context['vibe_scores']['N']}

DO NOT include: {context['do_not_play']}

You MUST output EXACTLY {num} tracks.
ZERO exceptions.
If you output fewer or more, the response is INVALID.

RETURN ONLY VALID JSON LIKE THIS (NO EXTRA TEXT):

{{
  "title": "Playlist title inspired by the vibe",
  "description": "One beautiful sentence",
  "tracks": [
    {{"artist": "Artist", "song": "Song"}},
    ... EXACTLY {num} total objects
  ]
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        temperature=0.7,
        messages=[
            {"role": "system", "content": "Return only perfect JSON. No markdown."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content
