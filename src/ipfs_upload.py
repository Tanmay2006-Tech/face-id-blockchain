"""
ipfs_upload.py
---------------
Pins the full match payload (not just its hash) to IPFS via Pinata's
free API, so the complete record is permanently retrievable by anyone
holding the CID — not just its fingerprint. The on-chain record stores
the CID + hash; IPFS stores the actual content, content-addressed (the
CID *is* a hash of the content, so IPFS itself is tamper-evident too —
this gives two independent layers of tamper-evidence).

Setup:
    1. Free account at https://pinata.cloud
    2. API Keys -> create a key with "pinFileToIPFS" / "pinJSONToIPFS" scope
    3. Set PINATA_JWT in .env

If PINATA_JWT is not set, the pipeline falls back to on-chain-hash-only
mode automatically (see pipeline.py) — IPFS is an enhancement, not a
hard requirement.

Usage:
    python ipfs_upload.py match_payload.json
"""

import os
import sys
import json
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

import requests

PINATA_JWT = os.environ.get("PINATA_JWT")
PINATA_PIN_JSON_URL = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
PUBLIC_GATEWAY = "https://gateway.pinata.cloud/ipfs/"


class IPFSNotConfiguredError(Exception):
    pass


def upload_payload(payload: dict, name: str = "face-match-record") -> dict:
    if not PINATA_JWT:
        raise IPFSNotConfiguredError(
            "PINATA_JWT not set — get a free key at pinata.cloud or run "
            "the pipeline without IPFS (on-chain hash only)."
        )

    body = {
        "pinataMetadata": {"name": name},
        "pinataContent": payload,
    }
    resp = requests.post(
        PINATA_PIN_JSON_URL,
        headers={"Authorization": f"Bearer {PINATA_JWT}"},
        json=body,
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    cid = data["IpfsHash"]

    return {
        "cid": cid,
        "gateway_url": PUBLIC_GATEWAY + cid,
        "pin_size": data.get("PinSize"),
        "timestamp": data.get("Timestamp"),
    }


def fetch_payload(cid: str) -> dict:
    """Retrieve content back from IPFS by CID, for verification."""
    resp = requests.get(PUBLIC_GATEWAY + cid, timeout=15)
    resp.raise_for_status()
    return resp.json()


def main():
    if len(sys.argv) != 2:
        print("Usage: python ipfs_upload.py <match_payload.json>")
        sys.exit(1)

    payload = json.loads(Path(sys.argv[1]).read_text())
    result = upload_payload(payload)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
