import random
import anthropic

GENRES = {
    "es": [
        "thriller urbano",
        "confesión anónima",
        "encontré esto en mi teléfono",
        "historia de miedo real",
        "secreto oscuro",
    ],
    "en": [
        "urban thriller",
        "anonymous confession",
        "found on my phone",
        "true horror story",
        "dark secret",
    ],
}

PROMPTS = {
    "es": (
        "Escribe una historia corta en primera persona del género '{genre}'. "
        "Reglas estrictas: empieza con un gancho poderoso en las primeras 2 oraciones, "
        "aproximadamente 130 palabras en total, punto de vista en primera persona, "
        "final con un giro inesperado. "
        "No incluyas título, introducción ni explicación. Solo el texto de la historia."
    ),
    "en": (
        "Write a short first-person story in the '{genre}' genre. "
        "Strict rules: start with a strong hook in the first 2 sentences, "
        "approximately 130 words total, first-person POV, unexpected twist ending. "
        "Do not include a title, introduction, or any explanation. Output only the story text."
    ),
}


def generate_story(api_key: str) -> tuple[str, str, str]:
    """Generate a story using Claude Haiku. Returns (story_text, lang, genre)."""
    lang = random.choice(list(GENRES.keys()))
    genre = random.choice(GENRES[lang])
    prompt = PROMPTS[lang].format(genre=genre)

    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )

    story_text = message.content[0].text.strip()
    print(f"  Genre: {genre} | Language: {lang} | Words: {len(story_text.split())}")
    return story_text, lang, genre


def generate_video_keyword(story_text: str, api_key: str) -> str:
    """Ask Claude for a Pexels search keyword that matches the story's mood and setting."""
    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=20,
        messages=[{
            "role": "user",
            "content": (
                "Read this story and reply with ONLY 2-3 words to search on Pexels for a "
                "background video that matches its mood, atmosphere and setting. "
                "Examples: 'dark city rain', 'forest night fog', 'abandoned corridor'. "
                "Reply with the search term only, no explanation.\n\n"
                f"Story: {story_text[:400]}"
            ),
        }],
    )

    keyword = message.content[0].text.strip().strip('"').strip("'").lower()
    print(f"  Video keyword: '{keyword}'")
    return keyword
