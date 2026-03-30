import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# moviepy 1.0.3 uses PIL.Image.ANTIALIAS which was removed in Pillow 10.
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.LANCZOS

from moviepy.editor import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    VideoClip,
    VideoFileClip,
)
from moviepy.video.fx.all import loop as fx_loop

VIDEO_W, VIDEO_H = 1080, 1920
FONT_SIZE = 90
STROKE_WIDTH = 3
OVERLAY_OPACITY = 0.45
SUBTITLE_Y_RATIO = 0.72  # How far down the screen the word appears


def _get_font(size: int = FONT_SIZE) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        os.path.join(os.path.dirname(__file__), "..", "assets", "fonts", "Impact.ttf"),
        "/usr/share/fonts/truetype/msttcorefonts/Impact.ttf",
        "/usr/share/fonts/truetype/impact.ttf",
        "/System/Library/Fonts/Supplemental/Impact.ttf",
        "/Library/Fonts/Impact.ttf",
        "C:/Windows/Fonts/Impact.ttf",
    ]
    for path in candidates:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            return ImageFont.truetype(abs_path, size)
    return ImageFont.load_default()


def _make_word_frame(word: str) -> np.ndarray:
    """Render a word as a full-frame RGBA numpy array (H x W x 4)."""
    img = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = _get_font(FONT_SIZE)

    bbox = draw.textbbox((0, 0), word, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    x = (VIDEO_W - text_w) // 2
    y = int(VIDEO_H * SUBTITLE_Y_RATIO) - text_h // 2

    for dx in range(-STROKE_WIDTH, STROKE_WIDTH + 1):
        for dy in range(-STROKE_WIDTH, STROKE_WIDTH + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), word, font=font, fill=(0, 0, 0, 255))

    draw.text((x, y), word, font=font, fill=(255, 255, 255, 255))
    return np.array(img)


def _make_subtitle_clip(
    word_timings: list[tuple[str, float, float]], duration: float
) -> VideoClip:
    """
    Build a single VideoClip that shows the correct word at each moment.
    Uses pre-rendered frames so make_frame is fast at render time.
    """
    # Pre-render every unique word once
    cache_rgb: dict[str, np.ndarray] = {}
    cache_alpha: dict[str, np.ndarray] = {}
    for word, _, _ in word_timings:
        if word not in cache_rgb:
            rgba = _make_word_frame(word)
            cache_rgb[word] = rgba[:, :, :3]
            # Normalise alpha to [0, 1] as moviepy expects for masks
            cache_alpha[word] = rgba[:, :, 3] / 255.0

    empty_rgb = np.zeros((VIDEO_H, VIDEO_W, 3), dtype=np.uint8)
    empty_alpha = np.zeros((VIDEO_H, VIDEO_W), dtype=np.float32)

    def get_rgb(t: float) -> np.ndarray:
        for word, start, end in word_timings:
            if start <= t < end:
                return cache_rgb[word]
        return empty_rgb

    def get_alpha(t: float) -> np.ndarray:
        for word, start, end in word_timings:
            if start <= t < end:
                return cache_alpha[word]
        return empty_alpha

    rgb_clip = VideoClip(get_rgb, duration=duration).set_fps(30)
    mask_clip = VideoClip(get_alpha, duration=duration, ismask=True).set_fps(30)
    return rgb_clip.set_mask(mask_clip)


def _crop_to_916(clip: VideoFileClip) -> VideoFileClip:
    """Center-crop clip to 9:16, then resize to 1080×1920."""
    w, h = clip.size
    target_ratio = VIDEO_W / VIDEO_H

    if abs(w / h - target_ratio) < 0.01:
        return clip.resize((VIDEO_W, VIDEO_H))

    if w / h > target_ratio:
        new_w = int(h * target_ratio)
        x1 = (w - new_w) // 2
        clip = clip.crop(x1=x1, y1=0, x2=x1 + new_w, y2=h)
    else:
        new_h = int(w / target_ratio)
        y1 = (h - new_h) // 2
        clip = clip.crop(x1=0, y1=y1, x2=w, y2=y1 + new_h)

    return clip.resize((VIDEO_W, VIDEO_H))


def assemble_video(
    story_text: str,
    word_timings: list[tuple[str, float, float]],
    voice_path: str = "output/voice.mp3",
    bg_path: str = "output/bg.mp4",
    output_path: str = "output/final.mp4",
) -> str:
    """Assemble the final TikTok video. Returns path to output file."""

    print("  Loading audio...")
    audio = AudioFileClip(voice_path)
    duration = audio.duration
    print(f"  Audio duration: {duration:.1f}s")

    print("  Loading background video...")
    bg_raw = VideoFileClip(bg_path, audio=False)
    print(f"  Background clip duration: {bg_raw.duration:.1f}s, size: {bg_raw.size}")

    # Loop background to match audio duration
    bg_looped = fx_loop(bg_raw, duration=duration).set_fps(30)

    print("  Cropping background to 9:16...")
    bg = _crop_to_916(bg_looped)

    overlay = (
        ColorClip(size=(VIDEO_W, VIDEO_H), color=[0, 0, 0])
        .set_duration(duration)
        .set_opacity(OVERLAY_OPACITY)
    )

    print(f"  Building karaoke subtitles for {len(word_timings)} words...")
    subtitle_clip = _make_subtitle_clip(word_timings, duration)

    print("  Compositing layers...")
    final = CompositeVideoClip(
        [bg, overlay, subtitle_clip],
        size=(VIDEO_W, VIDEO_H),
    ).set_audio(audio)

    print("  Rendering final video (this may take a minute)...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final.write_videofile(
        output_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=4,
        verbose=False,
        logger=None,
    )

    audio.close()
    bg_raw.close()

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  Saved final video to {output_path} ({size_mb:.1f} MB)")
    return output_path
