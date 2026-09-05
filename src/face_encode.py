"""
face_encode.py
--------------
Step 1 of the pipeline: detect a face in an input image and produce a
128-dimensional face encoding (embedding).

Uses `face_recognition` (built on dlib's ResNet-based face recognition
network). This is a real, widely-used face detection + encoding library
— not a mock.

Usage:
    python face_encode.py path/to/photo.jpg
"""

import sys
import json
import hashlib
from pathlib import Path

import face_recognition
import numpy as np


class NoFaceFoundError(Exception):
    pass


def encode_face(image_path: str) -> dict:
    """
    Detect the (first, largest) face in an image and return its
    128-d encoding plus useful metadata.
    """
    image_path = str(image_path)
    image = face_recognition.load_image_file(image_path)

    # HOG model is fast/CPU-friendly; swap to model="cnn" if a GPU is available
    # for higher accuracy.
    face_locations = face_recognition.face_locations(image, model="hog")

    if not face_locations:
        raise NoFaceFoundError(f"No face detected in {image_path}")

    # If multiple faces are found, pick the largest bounding box (assume
    # it's the primary subject of the photo).
    def area(loc):
        top, right, bottom, left = loc
        return (bottom - top) * (right - left)

    face_locations.sort(key=area, reverse=True)
    primary_location = face_locations[0]

    encodings = face_recognition.face_encodings(
        image, known_face_locations=[primary_location]
    )
    encoding = encodings[0]  # np.ndarray, shape (128,)

    # A short, stable fingerprint of the encoding — used later as the
    # on-chain identifier so we never have to put the raw biometric
    # vector itself on a public ledger.
    encoding_bytes = encoding.astype(np.float64).tobytes()
    encoding_hash = hashlib.sha256(encoding_bytes).hexdigest()

    return {
        "image_path": image_path,
        "face_location": {
            "top": primary_location[0],
            "right": primary_location[1],
            "bottom": primary_location[2],
            "left": primary_location[3],
        },
        "num_faces_detected": len(face_locations),
        "encoding": encoding.tolist(),
        "encoding_sha256": encoding_hash,
    }


def main():
    if len(sys.argv) != 2:
        print("Usage: python face_encode.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    if not Path(image_path).exists():
        print(f"Error: file not found: {image_path}")
        sys.exit(1)

    try:
        result = encode_face(image_path)
    except NoFaceFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Don't dump the full 128-float vector to stdout by default — just
    # the useful summary. Full result is returned to callers as a dict.
    summary = {k: v for k, v in result.items() if k != "encoding"}
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
