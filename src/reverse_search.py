"""
reverse_search.py
------------------
Step 2 of the pipeline: genuine reverse-image search.

Uses SerpApi's Google Lens API — a real, documented API that scrapes
live Google Lens results (not a mock, not hardcoded). It supports
uploading a local image file directly (no need to host it publicly
first), which goes through two calls:

    1. POST the image to SerpApi's Image API -> get an image_id
    2. GET the Google Lens search using that image_id -> visual_matches

Free tier: 250 searches/month, no credit card required to sign up.
Docs: https://serpapi.com/google-lens-api
      https://serpapi.com/image-api

Setup:
    1. Sign up free at https://serpapi.com (email + phone, no card)
    2. Copy your API key from the dashboard
    3. Set SERPAPI_KEY in .env

Usage:
    python reverse_search.py path/to/photo.jpg
"""

import os
import sys
import json
import io
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
load_dotenv()

import requests
from PIL import Image

SERPAPI_KEY = os.environ.get("SERPAPI_KEY")
IMAGE_UPLOAD_URL = "https://serpapi.com/image"
SEARCH_URL = "https://serpapi.com/search"
MAX_UPLOAD_BYTES = 500 * 1024  # SerpApi's Image API hard limit

SOCIAL_DOMAINS = (
    "instagram.com",
    "facebook.com",
    "twitter.com",
    "x.com",
    "linkedin.com",
    "tiktok.com",
    "reddit.com",
    "pinterest.com",
    "youtube.com",
    "threads.net",
)


class SerpApiNotConfiguredError(Exception):
    pass


def _is_social_url(url: str) -> bool:
    if not url:
        return False
    netloc = urlparse(url).netloc.lower()
    return any(domain in netloc for domain in SOCIAL_DOMAINS)


def _prepare_upload_bytes(image_path: str) -> tuple:
    """
    SerpApi's Image API caps uploads at 500KB and only accepts
    JPG/PNG/WebP. Most real photos (especially phone camera shots)
    exceed this, so we re-encode as JPEG and step down quality/size
    until it fits, rather than failing on a normal-sized photo.

    Returns (bytes, filename).
    """
    raw = Path(image_path).read_bytes()
    if len(raw) <= MAX_UPLOAD_BYTES:
        # Still worth confirming it's a supported format; if not, fall
        # through to the re-encode path below.
        suffix = Path(image_path).suffix.lower()
        if suffix in (".jpg", ".jpeg", ".png", ".webp"):
            return raw, Path(image_path).name

    img = Image.open(image_path).convert("RGB")

    # Downscale first if it's very large — faster convergence than
    # quality alone for big phone-camera images.
    max_dim = 1600
    if max(img.size) > max_dim:
        ratio = max_dim / max(img.size)
        img = img.resize((int(img.width * ratio), int(img.height * ratio)))

    for quality in (85, 75, 65, 55, 45, 35):
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        if buf.tell() <= MAX_UPLOAD_BYTES:
            return buf.getvalue(), "upload.jpg"

    # Last resort: shrink dimensions further at low quality.
    img = img.resize((img.width // 2, img.height // 2))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=35, optimize=True)
    return buf.getvalue(), "upload.jpg"


def _upload_image(image_path: str) -> str:
    """Upload a local image to SerpApi's Image API, return its image_id.
    The uploaded copy expires after 10 minutes on SerpApi's side and is
    only used to run the search below."""
    image_bytes, filename = _prepare_upload_bytes(image_path)
    resp = requests.post(
        IMAGE_UPLOAD_URL,
        files={"image": (filename, image_bytes)},
        data={"api_key": SERPAPI_KEY},
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    if "image_id" not in data:
        raise RuntimeError(f"SerpApi image upload failed: {data}")
    return data["image_id"]


def reverse_image_search(image_path: str) -> dict:
    """
    Run a genuine Google Lens reverse-image search on the given local
    image and return every visual match it found, flagging which ones
    look like social media posts/profiles.
    """
    if not SERPAPI_KEY:
        raise SerpApiNotConfiguredError(
            "SERPAPI_KEY not set. Sign up free at serpapi.com (no card "
            "required) and put your key in .env."
        )

    image_id = _upload_image(image_path)

    resp = requests.get(
        SEARCH_URL,
        params={
            "engine": "google_lens",
            "image_id": image_id,
            "type": "all",
            "api_key": SERPAPI_KEY,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    if "error" in data:
        raise RuntimeError(f"SerpApi error: {data['error']}")

    visual_matches = data.get("visual_matches", [])
    exact_matches = data.get("exact_matches", data.get("reverse_image_search", {}).get("exact_matches", []))
    all_matches = visual_matches + (exact_matches if isinstance(exact_matches, list) else [])

    pages = []
    for m in all_matches:
        pages.append(
            {
                "url": m.get("link"),
                "page_title": m.get("title"),
                "source": m.get("source"),
                "thumbnail": m.get("thumbnail"),
                "image": m.get("image"),
                "is_social_media": _is_social_url(m.get("link", "")),
            }
        )

    social_matches = [p for p in pages if p["is_social_media"] and p["url"]]

    # Full-resolution candidate image URLs (used by face_verify.py to
    # download and re-check faces) — prefer 'image' over 'thumbnail'.
    full_image_urls = [p["image"] or p["thumbnail"] for p in pages if (p["image"] or p["thumbnail"])]

    return {
        "image_path": str(image_path),
        "pages_with_matching_images": pages,
        "social_media_matches": social_matches,
        "full_matching_image_urls": full_image_urls,
        "partial_matching_image_urls": [],
        "best_guess_labels": [],
    }


def main():
    if len(sys.argv) != 2:
        print("Usage: python reverse_search.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    if not Path(image_path).exists():
        print(f"Error: file not found: {image_path}")
        sys.exit(1)

    result = reverse_image_search(image_path)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
