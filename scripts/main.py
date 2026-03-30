import os
import sys

# Allow running from any working directory
sys.path.insert(0, os.path.dirname(__file__))


def _load_env() -> None:
    """Load .env file if present (local dev). In CI, env vars come from secrets."""
    try:
        from dotenv import load_dotenv

        env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
        if os.path.exists(env_file):
            load_dotenv(env_file)
    except ImportError:
        pass  # python-dotenv not installed — rely on system env


def _require_env(*names: str) -> dict[str, str]:
    """Return a dict of env var values. Raises SystemExit if any are missing."""
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        print(f"[ERROR] Missing required environment variables: {', '.join(missing)}")
        print("  Set them in .env (local) or as repository secrets (CI).")
        sys.exit(1)
    return {n: os.environ[n] for n in names}


def _ensure_output_dir() -> None:
    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(output_dir, exist_ok=True)


def main() -> None:
    print("=== TikTok Story Bot ===\n")

    _load_env()
    env = _require_env("ANTHROPIC_API_KEY", "ELEVENLABS_API_KEY", "PEXELS_API_KEY")

    _ensure_output_dir()

    # Resolve output paths relative to repo root
    root = os.path.join(os.path.dirname(__file__), "..")
    voice_path = os.path.join(root, "output", "voice.mp3")
    bg_path = os.path.join(root, "output", "bg.mp4")
    final_path = os.path.join(root, "output", "final.mp4")

    # ── Step 1: Generate story ────────────────────────────────────────────────
    print("[1/4] Generating story with Claude Haiku...")
    try:
        from generate_story import generate_story, generate_video_keyword

        story_text, lang, genre = generate_story(env["ANTHROPIC_API_KEY"])
        print(f"  Story preview: {story_text[:80]}...")
        video_keyword = generate_video_keyword(story_text, env["ANTHROPIC_API_KEY"])
    except Exception as exc:
        print(f"[ERROR] Story generation failed: {exc}")
        sys.exit(1)

    # ── Step 2: Generate voice ────────────────────────────────────────────────
    print("\n[2/4] Generating voice with ElevenLabs...")
    try:
        from generate_voice import generate_voice

        _, word_timings = generate_voice(story_text, env["ELEVENLABS_API_KEY"], voice_path)
    except Exception as exc:
        print(f"[ERROR] Voice generation failed: {exc}")
        sys.exit(1)

    # ── Step 3: Fetch background video ───────────────────────────────────────
    print("\n[3/4] Fetching background video from Pexels...")
    try:
        from fetch_background import fetch_background

        fetch_background(env["PEXELS_API_KEY"], video_keyword, bg_path)
    except Exception as exc:
        print(f"[ERROR] Background fetch failed: {exc}")
        sys.exit(1)

    # ── Step 4: Assemble video ────────────────────────────────────────────────
    print("\n[4/4] Assembling final video...")
    try:
        from assemble_video import assemble_video

        assemble_video(story_text, word_timings, voice_path, bg_path, final_path)
    except Exception as exc:
        print(f"[ERROR] Video assembly failed: {exc}")
        sys.exit(1)

    print("\n=== Done! ===")
    print(f"Output: {os.path.abspath(final_path)}")


if __name__ == "__main__":
    main()
