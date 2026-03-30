import base64
import os
import requests

# Adam — ElevenLabs premade voice, available on free plan.
# Other free premade options: Antoni (ErXwobaYiN019PkySvjV), Bella (EXAVITQu4vr4xnSDxMaL)
# Override by setting ELEVENLABS_VOICE_ID in .env
DEFAULT_VOICE_ID = "pNInz6obpgDQGcFmaJgB"
MODEL_ID = "eleven_multilingual_v2"
API_BASE = "https://api.elevenlabs.io/v1"


def _chars_to_word_timings(alignment: dict) -> list[tuple[str, float, float]]:
    """Convert ElevenLabs character-level alignment into (word, start_sec, end_sec) tuples."""
    chars = alignment["characters"]
    starts = alignment["character_start_times_seconds"]
    ends = alignment["character_end_times_seconds"]

    words = []
    current_word = ""
    word_start = None
    last_end = 0.0

    for char, start, end in zip(chars, starts, ends):
        if char in (" ", "\n", "\t"):
            if current_word:
                words.append((current_word, word_start, last_end))
                current_word = ""
                word_start = None
        else:
            if not current_word:
                word_start = start
            current_word += char
        last_end = end

    if current_word:
        words.append((current_word, word_start, last_end))

    return words


def generate_voice(
    story_text: str,
    api_key: str,
    output_path: str = "output/voice.mp3",
) -> tuple[str, list[tuple[str, float, float]]]:
    """
    Convert text to speech using ElevenLabs with word-level timestamps.
    Returns (audio_path, word_timings) where word_timings = [(word, start_sec, end_sec), ...].
    """
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID", DEFAULT_VOICE_ID)
    url = f"{API_BASE}/text-to-speech/{voice_id}/with-timestamps"

    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
    }

    payload = {
        "text": story_text,
        "model_id": MODEL_ID,
        "voice_settings": {
            "stability": 0.4,
            "similarity_boost": 0.8,
            "style": 0.5,
        },
    }

    response = requests.post(url, json=payload, headers=headers, timeout=60)

    if response.status_code != 200:
        raise RuntimeError(
            f"ElevenLabs API error {response.status_code}: {response.text}"
        )

    data = response.json()
    audio_bytes = base64.b64decode(data["audio_base64"])

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(audio_bytes)

    word_timings = _chars_to_word_timings(data["alignment"])
    size_kb = len(audio_bytes) / 1024
    print(f"  Saved audio to {output_path} ({size_kb:.1f} KB, {len(word_timings)} words timed)")
    return output_path, word_timings
