"""
pipeline.py
-----------
End-to-end orchestrator:

    photo
      -> face_encode.py        (detect + encode source face)
      -> reverse_search.py     (genuine reverse-image search, Google
                                 Cloud Vision Web Detection)
      -> face_verify.py        (re-check: does the matched image
                                 actually contain the SAME face, not
                                 just a visually similar image?)
      -> ipfs_upload.py        (optional: pin full payload to IPFS)
      -> blockchain_writer.py  (write hash + CID to Polygon Amoy)
      -> verify_record.py      (re-fetch from chain and confirm it
                                 matches what we wrote — tamper-evidence
                                 proof, not just a write-and-forget)

Usage:
    python pipeline.py path/to/photo.jpg
    python pipeline.py path/to/photo.jpg --dry-run-chain
    python pipeline.py path/to/photo.jpg --no-ipfs
"""

import sys
import json
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from face_encode import encode_face, NoFaceFoundError
from reverse_search import reverse_image_search, SerpApiNotConfiguredError
from face_verify import verify_candidates
from blockchain_writer import write_record
from verify_record import verify as verify_onchain

console = Console()
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


def run_pipeline(image_path: str, dry_run_chain: bool = False, use_ipfs: bool = True):
    OUTPUT_DIR.mkdir(exist_ok=True)
    ts = int(time.time())

    console.rule("[bold cyan]STEP 1 — Face detection + encoding")
    face_result = encode_face(image_path)
    console.print(f"Faces detected: [bold]{face_result['num_faces_detected']}[/bold]")
    console.print(f"Face encoding SHA-256: [dim]{face_result['encoding_sha256']}[/dim]")

    console.rule("[bold cyan]STEP 2 — Genuine reverse-image search (Google Cloud Vision)")
    search_result = reverse_image_search(image_path)
    social_matches = search_result["social_media_matches"]

    if not social_matches:
        console.print("[yellow]No social media matches found for this image.[/yellow]")
        console.print(json.dumps(search_result["pages_with_matching_images"], indent=2))
        console.print("[red]Pipeline stopped — nothing genuine to write to chain.[/red]")
        return None

    console.print(f"Social media matches found: [bold]{len(social_matches)}[/bold]")
    for m in social_matches:
        console.print(f"  • {m['url']}")

    console.rule("[bold cyan]STEP 3 — Face re-verification of candidates")
    console.print("Downloading each candidate image and comparing its face embedding")
    console.print("to the source face — this checks it's the same PERSON, not just a")
    console.print("visually similar image.\n")

    candidate_urls = [m["url"] for m in social_matches] + search_result["full_matching_image_urls"]
    candidate_urls = list(dict.fromkeys(candidate_urls))  # dedupe, keep order

    verify_results = verify_candidates(face_result["encoding"], candidate_urls)

    table = Table(title="Face verification results")
    table.add_column("URL", overflow="fold")
    table.add_column("Face found")
    table.add_column("Distance")
    table.add_column("Verified match")
    for r in verify_results[:10]:
        table.add_row(
            r["url"],
            "yes" if r["face_found"] else "no",
            f"{r['distance']:.4f}" if r["distance"] is not None else "—",
            "[bold green]YES[/bold green]" if r["is_match"] else "no",
        )
    console.print(table)

    verified_matches = [r for r in verify_results if r["is_match"]]
    best_match_url = verified_matches[0]["url"] if verified_matches else social_matches[0]["url"]
    best_distance = verified_matches[0]["distance"] if verified_matches else None

    if verified_matches:
        console.print(f"\n[bold green]Verified face match:[/bold green] {best_match_url} "
                       f"(distance={best_distance:.4f})")
    else:
        console.print(
            "\n[yellow]No candidate passed face-verification threshold — "
            "recording the top reverse-image-search result, flagged as "
            "UNVERIFIED (image-level match only).[/yellow]"
        )

    matched_page_title = next(
        (m.get("page_title") for m in social_matches if m["url"] == best_match_url), None
    )

    match_payload = {
        "encoding_sha256": face_result["encoding_sha256"],
        "source_image": str(image_path),
        "matched_url": best_match_url,
        "matched_page_title": matched_page_title,
        "source_api": "serpapi-google-lens",
        "face_verified": bool(verified_matches),
        "face_match_distance": best_distance,
        "all_social_matches": [m["url"] for m in social_matches],
        "all_verification_results": verify_results,
        "timestamp_unix": ts,
    }

    console.rule("[bold cyan]STEP 4 — IPFS pin (full payload)")
    if use_ipfs:
        try:
            from ipfs_upload import upload_payload, IPFSNotConfiguredError
            ipfs_result = upload_payload(match_payload)
            match_payload["ipfs_cid"] = ipfs_result["cid"]
            console.print(f"Pinned to IPFS: [bold]{ipfs_result['cid']}[/bold]")
            console.print(f"Gateway: {ipfs_result['gateway_url']}")
        except IPFSNotConfiguredError:
            console.print("[yellow]PINATA_JWT not set — skipping IPFS pin "
                           "(on-chain will store hash only).[/yellow]")
            match_payload["ipfs_cid"] = ""
        except Exception as e:
            console.print(f"[yellow]IPFS pin failed ({e}) — continuing with hash only.[/yellow]")
            match_payload["ipfs_cid"] = ""
    else:
        match_payload["ipfs_cid"] = ""

    payload_path = OUTPUT_DIR / f"{ts}_match_payload.json"
    payload_path.write_text(json.dumps(match_payload, indent=2, sort_keys=True))
    console.print(f"Match payload saved: {payload_path}")

    if dry_run_chain:
        console.rule("[bold yellow]STEP 5 — Blockchain write SKIPPED (dry run)")
        return {"match_payload": match_payload, "chain_receipt": None}

    console.rule("[bold cyan]STEP 5 — Writing tamper-evident record to Polygon Amoy")
    receipt = write_record(match_payload)
    receipt_path = OUTPUT_DIR / f"{ts}_chain_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2))

    console.print(Panel.fit(
        f"[bold]Tx hash:[/bold] {receipt['tx_hash']}\n"
        f"[bold]Block:[/bold] {receipt['block_number']}\n"
        f"[bold]View on-chain:[/bold] {receipt['explorer_url']}",
        title="✅ On-chain record written", border_style="green",
    ))

    console.rule("[bold cyan]STEP 6 — Re-verifying against the on-chain record")
    import blockchain_writer as bw
    from web3 import Web3 as _W3
    w3 = _W3(_W3.HTTPProvider(bw.RPC_URL))
    contract = w3.eth.contract(address=_W3.to_checksum_address(bw.CONTRACT_ADDRESS), abi=bw.CONTRACT_ABI)
    record_id = contract.functions.totalRecords().call() - 1

    verify_result = verify_onchain(record_id, str(payload_path))
    if verify_result["verified"]:
        console.print(f"[bold green]✅ VERIFIED[/bold green] — record #{record_id} on-chain "
                       f"matches the local payload exactly.")
    else:
        console.print(f"[bold red]❌ MISMATCH[/bold red] on record #{record_id} — investigate.")

    return {
        "match_payload": match_payload,
        "chain_receipt": receipt,
        "record_id": record_id,
        "onchain_verification": verify_result,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <image_path> [--dry-run-chain] [--no-ipfs]")
        sys.exit(1)

    image_path = sys.argv[1]
    dry_run = "--dry-run-chain" in sys.argv
    no_ipfs = "--no-ipfs" in sys.argv

    if not Path(image_path).exists():
        print(f"Error: file not found: {image_path}")
        sys.exit(1)

    try:
        run_pipeline(image_path, dry_run_chain=dry_run, use_ipfs=not no_ipfs)
    except NoFaceFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except SerpApiNotConfiguredError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
