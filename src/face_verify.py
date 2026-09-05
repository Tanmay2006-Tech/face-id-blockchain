"""
face_verify.py
---------------
This is the piece that actually makes this a *face identification*
pipeline rather than a generic reverse-image search.

Google Vision's Web Detection tells you an image looks similar
somewhere on the web — it does NOT tell you the face in that matched
image is the same person. This module closes that gap: it downloads
each candidate matching image, runs the same face detection/encoding
used on the source photo, and computes the actual face-embedding
distance between the source face and each candidate. Only candidates
below a distance threshold (i.e. a real face match, not just visual
similarity) are surfaced.

This is what lets the pipeline claim "verified face match" rather than
"an image that looks similar was found somewhere."
"""

import io
import sys
import json
from pathlib import Path
from typing import Optional

import requests
import face_recognition
import numpy as np

# face_recognition's standard rule of thumb: distance < 0.6 is
# considered the same person. We use a slightly stricter default for
# higher-confidence claims.
DEFAULT_MATCH_THRESHOLD = 0.55
REQUEST_TIMEOUT_SECONDS = 8
USER_AGENT = "face-id-blockchain-pipeline/1.0 (verification research tool)"


def _download_image(url: str) -> Optional[bytes]:
    try:
        resp = requests.get(
            url,
            timeout=REQUEST_TIMEOUT_SECONDS,
            headers={"User-Agent": USER_AGENT},
        )
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "")
        if "image" not in content_type:
            return None
        return resp.content
    except requests.RequestException:
        return None


def _encode_from_bytes(image_bytes: bytes) -> Optional[np.ndarray]:
    try:
        image = face_recognition.load_image_file(io.BytesIO(image_bytes))
    except Exception:
        return None

    locations = face_recognition.face_locations(image, model="hog")
    if not locations:
        return None

    # Largest face in the candidate image
    def area(loc):
        top, right, bottom, left = loc
        return (bottom - top) * (right - left)

    locations.sort(key=area, reverse=True)
    encodings = face_recognition.face_encodings(image, known_face_locations=[locations[0]])
    if not encodings:
        return None
    return encodings[0]


def verify_candidates(
    source_encoding: np.ndarray,
    candidate_image_urls: list,
    threshold: float = DEFAULT_MATCH_THRESHOLD,
) -> list:
    """
    For each candidate image URL, download it, detect/encode its face,
    and compute the distance to the source face encoding.

    Returns a list of dicts sorted by ascending distance (best match
    first), each with: url, face_found, distance, is_match.
    """
    source_encoding = np.asarray(source_encoding)
    results = []

    for url in candidate_image_urls:
        image_bytes = _download_image(url)
        if image_bytes is None:
            results.append(
                {"url": url, "face_found": False, "distance": None, "is_match": False,
                 "note": "could not download or not an image"}
            )
            continue

        candidate_encoding = _encode_from_bytes(image_bytes)
        if candidate_encoding is None:
            results.append(
                {"url": url, "face_found": False, "distance": None, "is_match": False,
                 "note": "no face detected in candidate image"}
            )
            continue

        distance = float(
            np.linalg.norm(source_encoding - candidate_encoding)
        )
        results.append(
            {
                "url": url,
                "face_found": True,
                "distance": round(distance, 4),
                "is_match": distance < threshold,
            }
        )

    results.sort(key=lambda r: (r["distance"] is None, r["distance"] if r["distance"] is not None else 999))
    return results


def main():
    # Standalone test harness: python face_verify.py source.jpg url1 url2 ...
    if len(sys.argv) < 3:
        print("Usage: python face_verify.py <source_image> <candidate_url> [more urls...]")
        sys.exit(1)

    from face_encode import encode_face

    source = encode_face(sys.argv[1])
    urls = sys.argv[2:]
    results = verify_candidates(np.array(source["encoding"]), urls)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
