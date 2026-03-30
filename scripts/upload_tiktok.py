"""
TikTok upload stub.

TikTok does not offer a public one-click upload API for personal accounts.
To automate posting you have two legitimate paths:

──────────────────────────────────────────────────────────────────────────────
OPTION 1 — TikTok Content Posting API (Business / Creator accounts)
──────────────────────────────────────────────────────────────────────────────
1. Apply for API access at https://developers.tiktok.com/
2. Create an app and request the `video.upload` and `video.publish` scopes.
3. Complete the OAuth 2.0 flow to obtain an `access_token` for your account.
4. Use the two-step Direct Post flow:
   a. POST https://open.tiktokapis.com/v2/post/publish/video/init/
      with {post_info: {title, privacy_level}, source_info: {source: "FILE_UPLOAD"}}
      → you receive an `upload_url` and a `publish_id`
   b. PUT <upload_url>  with the raw video bytes + required headers
      (Content-Type: video/mp4, Content-Range, Content-Length)
5. Poll GET https://open.tiktokapis.com/v2/post/publish/status/fetch/
   with the `publish_id` until status is "PUBLISH_COMPLETE".

Reference: https://developers.tiktok.com/doc/content-posting-api-get-started

──────────────────────────────────────────────────────────────────────────────
OPTION 2 — TikTok for Developers "Share" (mobile / desktop app)
──────────────────────────────────────────────────────────────────────────────
Use the Share SDK in a mobile app (iOS/Android) to let the user share directly
from within your app. Not applicable to server-side automation.

──────────────────────────────────────────────────────────────────────────────
STUB IMPLEMENTATION (replace with real credentials / flow)
──────────────────────────────────────────────────────────────────────────────
"""

import os
import requests


def upload_to_tiktok(video_path: str, title: str, access_token: str) -> str:
    """
    Stub: upload video_path to TikTok using the Content Posting API.

    Returns the publish_id on success.

    Before using this function you must:
    - Complete OAuth and obtain `access_token` with video.upload + video.publish scopes.
    - Ensure your TikTok app has Content Posting API access approved.
    """
    if not access_token:
        raise RuntimeError(
            "TIKTOK_ACCESS_TOKEN is not set. "
            "Complete the OAuth flow described in this file first."
        )

    # Step 1: Initialise the upload
    init_url = "https://open.tiktokapis.com/v2/post/publish/video/init/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }
    video_size = os.path.getsize(video_path)
    init_payload = {
        "post_info": {
            "title": title[:150],  # max 150 chars
            "privacy_level": "SELF_ONLY",  # change to PUBLIC_TO_EVERYONE when ready
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": video_size,
            "chunk_size": video_size,
            "total_chunk_count": 1,
        },
    }

    init_resp = requests.post(init_url, json=init_payload, headers=headers, timeout=30)
    if init_resp.status_code != 200:
        raise RuntimeError(f"TikTok init error {init_resp.status_code}: {init_resp.text}")

    data = init_resp.json().get("data", {})
    upload_url = data.get("upload_url")
    publish_id = data.get("publish_id")

    if not upload_url or not publish_id:
        raise RuntimeError(f"Unexpected TikTok init response: {init_resp.text}")

    # Step 2: Upload the video bytes
    with open(video_path, "rb") as f:
        video_bytes = f.read()

    upload_headers = {
        "Content-Type": "video/mp4",
        "Content-Range": f"bytes 0-{video_size - 1}/{video_size}",
        "Content-Length": str(video_size),
    }
    upload_resp = requests.put(upload_url, data=video_bytes, headers=upload_headers, timeout=120)
    if upload_resp.status_code not in (200, 201):
        raise RuntimeError(f"TikTok upload error {upload_resp.status_code}: {upload_resp.text}")

    print(f"  Video uploaded. Publish ID: {publish_id}")
    print("  Check publish status at: https://open.tiktokapis.com/v2/post/publish/status/fetch/")
    return publish_id
