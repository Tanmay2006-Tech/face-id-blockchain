"""
verify_record.py
------------------
Proves the tamper-evidence claim: takes a record ID (from a chain
receipt) and a local match_payload.json, re-fetches the record from
the blockchain, recomputes both hashes locally, and confirms they
match what's on-chain. If anyone had altered the saved JSON file after
the fact, this would fail.

This is the "re-verify against the on-chain record" step your task
requires — run this in your demo right after the upload, ideally after
editing the JSON file by one character first to show a FAIL case too.

Usage:
    python verify_record.py <record_id> <match_payload.json>
"""

import sys
import json
import hashlib
from pathlib import Path

from blockchain_writer import get_record


def verify(record_id: int, payload_path: str) -> dict:
    match_payload = json.loads(Path(payload_path).read_text())

    onchain = get_record(record_id)

    # Recompute both hashes exactly as blockchain_writer.py did at write time
    local_face_hash = match_payload["encoding_sha256"]
    canonical_payload = json.dumps(match_payload, sort_keys=True).encode("utf-8")
    local_payload_hash = hashlib.sha256(canonical_payload).hexdigest()

    face_hash_match = local_face_hash == onchain["face_encoding_hash"].replace("0x", "")
    payload_hash_match = local_payload_hash == onchain["match_payload_hash"].replace("0x", "")

    url_match = match_payload.get("matched_url") == onchain["matched_url"]

    verified = face_hash_match and payload_hash_match and url_match

    return {
        "record_id": record_id,
        "verified": verified,
        "checks": {
            "face_encoding_hash_matches": face_hash_match,
            "payload_hash_matches": payload_hash_match,
            "matched_url_matches": url_match,
        },
        "local": {
            "face_encoding_hash": local_face_hash,
            "payload_hash": local_payload_hash,
        },
        "onchain": onchain,
    }


def main():
    if len(sys.argv) != 3:
        print("Usage: python verify_record.py <record_id> <match_payload.json>")
        sys.exit(1)

    record_id = int(sys.argv[1])
    result = verify(record_id, sys.argv[2])

    print(json.dumps(result, indent=2))
    print()
    if result["verified"]:
        print("✅ VERIFIED — local data matches the on-chain tamper-evident record.")
    else:
        print("❌ MISMATCH — local data does NOT match the on-chain record.")
        print("   (Either the file was altered, or the wrong record_id was given.)")
        sys.exit(2)


if __name__ == "__main__":
    main()
