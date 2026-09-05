"""
blockchain_writer.py
---------------------
Write a tamper-evident face-match record to Polygon Amoy.

What goes on-chain:
    - sha256(face_encoding)
    - sha256(full_match_payload)
    - matched_url
    - source_api
    - IPFS CID
    - face-match distance

Environment variables required:
    RPC_URL
    CHAIN_ID
    PRIVATE_KEY
    CONTRACT_ADDRESS

Usage:
    python blockchain_writer.py match_payload.json
"""

import os
import sys
import json
import hashlib
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

RPC_URL = os.environ.get(
    "RPC_URL",
    "https://polygon-amoy.drpc.org"
)

CHAIN_ID = int(
    os.environ.get("CHAIN_ID", "80002")
)

PRIVATE_KEY = os.environ.get("PRIVATE_KEY")

CONTRACT_ADDRESS = os.environ.get("CONTRACT_ADDRESS")


# -------------------------------------------------------------------
# FaceRecord Contract ABI
# -------------------------------------------------------------------

CONTRACT_ABI = json.loads("""
[
  {
    "inputs": [
      {
        "internalType": "bytes32",
        "name": "faceEncodingHash",
        "type": "bytes32"
      },
      {
        "internalType": "bytes32",
        "name": "matchPayloadHash",
        "type": "bytes32"
      },
      {
        "internalType": "string",
        "name": "matchedUrl",
        "type": "string"
      },
      {
        "internalType": "string",
        "name": "matchSourceApi",
        "type": "string"
      },
      {
        "internalType": "string",
        "name": "ipfsCid",
        "type": "string"
      },
      {
        "internalType": "uint256",
        "name": "faceMatchDistanceScaled",
        "type": "uint256"
      }
    ],
    "name": "addRecord",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "recordId",
        "type": "uint256"
      }
    ],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "recordId",
        "type": "uint256"
      }
    ],
    "name": "getRecord",
    "outputs": [
      {
        "components": [
          {
            "internalType": "bytes32",
            "name": "faceEncodingHash",
            "type": "bytes32"
          },
          {
            "internalType": "bytes32",
            "name": "matchPayloadHash",
            "type": "bytes32"
          },
          {
            "internalType": "string",
            "name": "matchedUrl",
            "type": "string"
          },
          {
            "internalType": "string",
            "name": "matchSourceApi",
            "type": "string"
          },
          {
            "internalType": "string",
            "name": "ipfsCid",
            "type": "string"
          },
          {
            "internalType": "uint256",
            "name": "faceMatchDistance",
            "type": "uint256"
          },
          {
            "internalType": "uint256",
            "name": "timestamp",
            "type": "uint256"
          },
          {
            "internalType": "address",
            "name": "submittedBy",
            "type": "address"
          }
        ],
        "internalType": "struct FaceRecord.Record",
        "name": "",
        "type": "tuple"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "totalRecords",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "anonymous": false,
    "inputs": [
      {
        "indexed": true,
        "internalType": "uint256",
        "name": "recordId",
        "type": "uint256"
      },
      {
        "indexed": true,
        "internalType": "bytes32",
        "name": "faceEncodingHash",
        "type": "bytes32"
      },
      {
        "indexed": false,
        "internalType": "string",
        "name": "matchedUrl",
        "type": "string"
      },
      {
        "indexed": false,
        "internalType": "string",
        "name": "ipfsCid",
        "type": "string"
      },
      {
        "indexed": false,
        "internalType": "uint256",
        "name": "timestamp",
        "type": "uint256"
      }
    ],
    "name": "RecordAdded",
    "type": "event"
  }
]
""")


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def _sha256_hex_to_bytes32(hex_str: str) -> bytes:
    """
    Convert a 64-character SHA-256 hex string into bytes32.
    """
    return bytes.fromhex(hex_str)


def _create_web3() -> Web3:
    """
    Create a Web3 connection configured for Polygon Amoy.

    Polygon Amoy can return PoA-style extraData in blocks.
    ExtraDataToPOAMiddleware handles that correctly.
    """

    w3 = Web3(
        Web3.HTTPProvider(RPC_URL)
    )

    # IMPORTANT:
    # Must be injected at layer 0.
    w3.middleware_onion.inject(
        ExtraDataToPOAMiddleware,
        layer=0
    )

    if not w3.is_connected():
        raise RuntimeError(
            f"Could not connect to RPC endpoint: {RPC_URL}"
        )

    return w3


# -------------------------------------------------------------------
# Write record to blockchain
# -------------------------------------------------------------------

def write_record(match_payload: dict) -> dict:
    """
    Write a tamper-evident record for one reverse-image-search
    match to the FaceRecord contract on Polygon Amoy.

    Expected keys in match_payload:
        - encoding_sha256
        - matched_url
        - source_api
        - face_match_distance

    Additional fields are included in the payload hash.
    """

    # ---------------------------------------------------------------
    # Check environment variables
    # ---------------------------------------------------------------

    if not PRIVATE_KEY:
        raise RuntimeError(
            "PRIVATE_KEY is missing from environment variables."
        )

    if not CONTRACT_ADDRESS:
        raise RuntimeError(
            "CONTRACT_ADDRESS is missing from environment variables."
        )

    # ---------------------------------------------------------------
    # Connect to Polygon
    # ---------------------------------------------------------------

    w3 = _create_web3()

    # ---------------------------------------------------------------
    # Create account
    # ---------------------------------------------------------------

    account = w3.eth.account.from_key(
        PRIVATE_KEY
    )

    print(
        f"Blockchain account: {account.address}"
    )

    # ---------------------------------------------------------------
    # Create contract instance
    # ---------------------------------------------------------------

    contract = w3.eth.contract(
        address=Web3.to_checksum_address(
            CONTRACT_ADDRESS
        ),
        abi=CONTRACT_ABI
    )

    # ---------------------------------------------------------------
    # Face encoding hash
    # ---------------------------------------------------------------

    face_encoding_hash = _sha256_hex_to_bytes32(
        match_payload["encoding_sha256"]
    )

    # ---------------------------------------------------------------
    # Canonical JSON payload hash
    # ---------------------------------------------------------------

    canonical_payload = json.dumps(
        match_payload,
        sort_keys=True
    ).encode("utf-8")

    match_payload_hash = hashlib.sha256(
        canonical_payload
    ).digest()

    # ---------------------------------------------------------------
    # Values stored on-chain
    # ---------------------------------------------------------------

    matched_url = match_payload.get(
        "matched_url",
        ""
    )

    source_api = match_payload.get(
        "source_api",
        "serpapi-google-lens"
    )

    ipfs_cid = match_payload.get(
        "ipfs_cid",
        ""
    )

    # ---------------------------------------------------------------
    # Scale face distance
    #
    # Example:
    #     0.123456
    #
    # becomes:
    #     123456
    #
    # because Solidity uint256 cannot store Python floats.
    # ---------------------------------------------------------------

    raw_distance = match_payload.get(
        "face_match_distance"
    )

    if raw_distance is not None:
        face_match_distance_scaled = int(
            round(raw_distance * 1_000_000)
        )
    else:
        face_match_distance_scaled = 0

    # ---------------------------------------------------------------
    # Get nonce
    # ---------------------------------------------------------------

    nonce = w3.eth.get_transaction_count(
        account.address
    )

    # ---------------------------------------------------------------
    # Build transaction
    # ---------------------------------------------------------------

    tx = contract.functions.addRecord(
        face_encoding_hash,
        match_payload_hash,
        matched_url,
        source_api,
        ipfs_cid,
        face_match_distance_scaled,
    ).build_transaction(
        {
            "chainId": CHAIN_ID,
            "from": account.address,
            "nonce": nonce,
        }
    )

    # ---------------------------------------------------------------
    # Sign transaction
    # ---------------------------------------------------------------

    signed_tx = w3.eth.account.sign_transaction(
        tx,
        private_key=PRIVATE_KEY
    )

    # ---------------------------------------------------------------
    # Send transaction
    # ---------------------------------------------------------------

    tx_hash = w3.eth.send_raw_transaction(
        signed_tx.raw_transaction
    )

    print(
        f"Transaction submitted: {tx_hash.hex()}"
    )

    # ---------------------------------------------------------------
    # Wait for confirmation
    # ---------------------------------------------------------------

    receipt = w3.eth.wait_for_transaction_receipt(
        tx_hash
    )

    # ---------------------------------------------------------------
    # Explorer URL
    # ---------------------------------------------------------------

    explorer_base = (
        "https://amoy.polygonscan.com/tx/"
    )

    tx_hash_hex = receipt.transactionHash.hex()

    # ---------------------------------------------------------------
    # Return result
    # ---------------------------------------------------------------

    return {
        "tx_hash": tx_hash_hex,
        "block_number": receipt.blockNumber,
        "status": (
            "success"
            if receipt.status == 1
            else "failed"
        ),
        "explorer_url": (
            explorer_base + tx_hash_hex
        ),
        "face_encoding_hash_hex": (
            face_encoding_hash.hex()
        ),
        "match_payload_hash_hex": (
            match_payload_hash.hex()
        ),
    }


# -------------------------------------------------------------------
# Read record from blockchain
# -------------------------------------------------------------------

def get_record(record_id: int) -> dict:
    """
    Read a record back from Polygon Amoy by its ID.
    Used for on-chain verification.
    """

    # IMPORTANT:
    # Use the same POA middleware here as well.
    w3 = _create_web3()

    contract = w3.eth.contract(
        address=Web3.to_checksum_address(
            CONTRACT_ADDRESS
        ),
        abi=CONTRACT_ABI
    )

    record = contract.functions.getRecord(
        record_id
    ).call()

    return {
        "face_encoding_hash": record[0].hex(),
        "match_payload_hash": record[1].hex(),
        "matched_url": record[2],
        "match_source_api": record[3],
        "ipfs_cid": record[4],
        "face_match_distance_scaled": record[5],
        "timestamp": record[6],
        "submitted_by": record[7],
    }


# -------------------------------------------------------------------
# Command-line entry point
# -------------------------------------------------------------------

def main():

    if len(sys.argv) != 2:
        print(
            "Usage: python blockchain_writer.py "
            "<match_payload.json>"
        )
        sys.exit(1)

    payload_path = Path(
        sys.argv[1]
    )

    if not payload_path.exists():
        print(
            f"Error: file not found: {payload_path}"
        )
        sys.exit(1)

    try:

        match_payload = json.loads(
            payload_path.read_text(
                encoding="utf-8"
            )
        )

        result = write_record(
            match_payload
        )

        print(
            json.dumps(
                result,
                indent=2
            )
        )

    except Exception as e:

        print(
            f"Blockchain error: {e}"
        )

        raise


if __name__ == "__main__":
    main()