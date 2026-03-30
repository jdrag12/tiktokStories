import os
import random
import requests

PEXELS_VIDEOS_API = "https://api.pexels.com/videos/search"
FALLBACK_KEYWORD = "dark city night"


def _pick_portrait_file(video: dict) -> str | None:
    """Return the URL of the best portrait video file, or None."""
    portrait = [
        vf for vf in video.get("video_files", [])
        if vf.get("height", 0) > vf.get("width", 0)
        and vf.get("quality") in ("hd", "sd", "uhd")
    ]
    if portrait:
        portrait.sort(
            key=lambda x: {"uhd": 3, "hd": 2, "sd": 1}.get(x.get("quality"), 0),
            reverse=True,
        )
        return portrait[0]["link"]
    files = video.get("video_files", [])
    return files[0]["link"] if files else None


def _search(api_key: str, keyword: str) -> list[dict]:
    headers = {"Authorization": api_key}
    params = {"query": keyword, "orientation": "portrait", "per_page": 15}
    response = requests.get(PEXELS_VIDEOS_API, headers=headers, params=params, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(f"Pexels API error {response.status_code}: {response.text}")
    return response.json().get("videos", [])


def fetch_background(api_key: str, keyword: str = "", output_path: str = "output/bg.mp4") -> str:
    """Download a background video from Pexels using the given keyword."""
    if not keyword:
        keyword = FALLBACK_KEYWORD

    print(f"  Searching Pexels for: '{keyword}'")
    videos = _search(api_key, keyword)

    if not videos:
        print(f"  No results — retrying with fallback: '{FALLBACK_KEYWORD}'")
        videos = _search(api_key, FALLBACK_KEYWORD)

    if not videos:
        raise RuntimeError(f"No videos found on Pexels for keyword: '{keyword}'")

    random.shuffle(videos)
    video_url = None
    for video in videos:
        video_url = _pick_portrait_file(video)
        if video_url:
            break

    if not video_url:
        raise RuntimeError("Could not find a suitable video file in Pexels results.")

    print("  Downloading video...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with requests.get(video_url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  Saved background to {output_path} ({size_mb:.1f} MB)")
    return output_path
