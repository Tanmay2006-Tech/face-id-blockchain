# Face ID Blockchain

> **HH Goa 2026 — Task #3: Face Identification & Blockchain Verification**

An end-to-end pipeline that takes a face scan as input, finds a genuine matching post on the web/social media via reverse image search, re-verifies that the match is actually the same person using facial embeddings, and creates a tamper-evident, on-chain record of the discovered evidence on the Polygon Amoy blockchain.

**Pipeline shape:** Face scan → Web/social media search (find matching post) → Blockchain upload & verification of the discovered data.

---

## 🚀 Overview

```text
Face Image
    │
    ▼
Face Detection & Encoding
    │
    ▼
Reverse Image Search (live web/social search)
    │
    ▼
Candidate Images
    │
    ▼
Face Re-verification (embedding comparison)
    │
    ▼
Best Verified Match
    │
    ├──────────────► IPFS Evidence Archive
    │
    ▼
Tamper-Evident Blockchain Record (Polygon Amoy)
    │
    ▼
On-chain Verification
```

The system combines computer vision, a genuine live web search, decentralized storage, and blockchain verification into a single pipeline — no hardcoded or pre-picked matches.

## ✨ Features

- 🧑‍💻 Face detection and facial embedding generation
- 🔍 Live reverse image search for discovering potential matches (not hardcoded)
- 🧠 Facial embedding comparison to confirm the same person, not just visual similarity
- 🌐 Web and social-media candidate discovery
- 📦 Complete match payload archived on IPFS
- ⛓️ Tamper-evident record stored on Polygon Amoy
- 🔐 SHA-256 hashing of face encoding and match payload
- ✅ Automatic re-verification of local data against the on-chain record
- 🧪 Dry-run mode for testing without blockchain submission

## 🏗️ Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Face Recognition | `face_recognition` / `dlib` |
| Reverse Image Search | Google Cloud Vision |
| Decentralized Storage | Pinata / IPFS |
| Blockchain | **Polygon Amoy** (public EVM testnet) |
| Smart Contract | Solidity |
| Blockchain Development | Hardhat |
| Python Blockchain Client | Web3.py |
| Environment Management | python-dotenv |

## 📁 Project Structure

```text
face-id-blockchain/
│
├── contract/
│   └── FaceRecord.sol
│
├── contracts/
│   ├── Counter.sol
│   ├── Counter.t.sol
│   └── FaceRecord.sol
│
├── scripts/
│   ├── deploy.ts
│   └── send-op-tx.ts
│
├── src/
│   ├── blockchain_writer.py
│   ├── face_encode.py
│   ├── face_verify.py
│   ├── ipfs_upload.py
│   ├── pipeline.py
│   ├── reverse_search.py
│   └── verify_record.py
│
├── test/
│   └── Counter.ts
│
├── types/
│   └── ethers-contracts/       # TypeChain-generated contract bindings
│
├── output/
│   └── match_payload.json      # generated per run (timestamped)
│
├── test_face.jpg
├── hardhat.config.ts
├── package.json
├── requirements.txt
├── .env.example
└── README.md
```

## 🔄 Pipeline

### 1. Face Detection & Encoding

The input image is processed using `face_recognition` and `dlib`.

The system:

- Detects faces in the image.
- Generates a facial embedding.
- Calculates a SHA-256 hash of the encoding.
- Uses the encoding as the reference for subsequent verification.

Example:

```text
Faces detected: 1

Face encoding SHA-256:
90c6c90651f0d9f692b202857dca262e151345b2b81417bf787424d30a0ad868
```

### 2. Reverse Image Search

The reference image is submitted to the reverse-image-search component (`reverse_search.py`), which performs a **live** web/social media search — this is a genuine query on every run, not a hardcoded or pre-selected result.

Example output:

```text
Social media matches found: 16
```

The results are treated as candidates, not as confirmed identity matches.

### 3. Face Re-verification

Each candidate image is downloaded and analyzed. The candidate's facial embedding is compared with the original face embedding — a lower face distance indicates a closer facial embedding match.

Example:

```text
Face verification results

Distance: 0.0000
Verified match: YES
```

This step prevents the pipeline from trusting reverse-image-search results on visual similarity alone; it confirms the match is actually the same person.

### 4. IPFS Evidence Archive

Once a verified match is selected, the complete match payload is uploaded to IPFS through Pinata. The IPFS CID provides a content-addressed reference to the archived evidence.

Example:

```text
Pinned to IPFS:
QmX6ghcqhvw0jUtCYRsrL1CBxXaRPTN2FvwZhw1QdbevCH
```

Gateway: `https://gateway.pinata.cloud/ipfs/QmX6ghcqhvw0jUtCYRsrL1CBxXaRPTN2FvwZhw1QdbevCH`

### 5. Blockchain Upload & Verification

The project uses a Solidity smart contract deployed on **Polygon Amoy** (public EVM testnet, Chain ID `80002`).

- **Contract address:** `0xEE30E6f46A892bd222DFa43BbE34c86C3042f188`

The blockchain record stores cryptographic references rather than the original face image itself. The contract records:

- Face encoding SHA-256
- Match payload SHA-256
- Matched URL
- Reverse-search source
- IPFS CID
- Face-match distance
- Timestamp
- Submitting wallet address

### 6. On-Chain Re-verification

After submitting the blockchain transaction, `verify_record.py` reads the record back from the smart contract and compares it against the local payload.

Successful execution produces:

```text
✓ On-chain record written
✓ VERIFIED — record #0 on-chain matches the local payload exactly.
```

This gives an end-to-end verification path from the original face scan all the way to the on-chain record.

## 🔐 Tamper-Evident Design

The system generates two hashes — `SHA-256(face encoding)` and `SHA-256(canonical match payload)` — which are recorded on-chain. The complete payload itself is stored on IPFS.

```text
Local Face Encoding ──▶ SHA-256 ──▶ Blockchain Record
Match Payload       ──▶ SHA-256 ──▶ Blockchain Record
Match Payload       ──▶ IPFS ──▶ CID ──▶ Blockchain Record
```

If the local payload is modified after submission, its recomputed hash no longer matches the hash stored on-chain — making tampering detectable.

## 🧪 Running the Project

### 1. Clone the repository

```bash
git clone https://github.com/Tanmay2006-Tech/face-id-blockchain.git
cd face-id-blockchain
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Node dependencies

```bash
npm install
```

### 4. Configure environment variables

Create a `.env` file in the project root (see `.env.example`):

```env
SERPAPI_KEY=your_key
RPC_URL=https://polygon-amoy.drpc.org
CHAIN_ID=80002
PRIVATE_KEY=your_wallet_private_key
CONTRACT_ADDRESS=0xEE30E6f46A892bd222DFa43BbE34c86C3042f188
PINATA_JWT=your_pinata_jwt
```

> ⚠️ Never commit `.env`, private keys, or API keys to GitHub.

### 5. Run the pipeline

Place an input image in the project directory and run:

```bash
python src/pipeline.py test_face.jpg
```

The pipeline performs:

```text
STEP 1 - Face detection + encoding
STEP 2 - Reverse-image search (live)
STEP 3 - Face re-verification
STEP 4 - IPFS pin
STEP 5 - Polygon Amoy blockchain write
STEP 6 - On-chain re-verification
```

### 🧪 Dry run (no blockchain write)

```bash
python src/pipeline.py test_face.jpg --dry-run-chain
```

To skip IPFS:

```bash
python src/pipeline.py test_face.jpg --no-ipfs
```

## 📜 Smart Contract

`FaceRecord.sol` provides:

- `addRecord(...)`
- `getRecord(...)`
- `totalRecords()`

Each submitted record receives a sequential record ID. The `RecordAdded` event provides an auditable on-chain event with the record information.

- Deploy: `scripts/deploy.ts`
- Send a raw transaction: `scripts/send-op-tx.ts`
- Sample tests: `test/Counter.ts`
- TypeChain bindings: `types/ethers-contracts/`

## 🌐 Example Blockchain Transaction

```text
Transaction:
98b9ec3e8a1239ac188373460ec55080cb842ada98e9363421e1ce3a1c23f23d

Block:
46797023
```

View on PolygonScan: `https://amoy.polygonscan.com/tx/98b9ec3e8a1239ac188373460ec55080cb842ada98e9363421e1ce3a1c23f23d`

## 🎯 Hackathon Requirement Mapping

| HH Goa Task Requirement | Implementation |
|---|---|
| Face detection & encoding | `face_encode.py` |
| Genuine, non-hardcoded web/social search | `reverse_search.py` (live query per run) |
| Blockchain upload of discovered data (hash/fingerprint) | `blockchain_writer.py` → Polygon Amoy |
| Re-verify data against the on-chain record | `verify_record.py` |
| No website required | N/A — not built |
| Full source in GitHub repo | This repository |
| README: what it does, how to run, blockchain used, limitations | This document |

## ⚠️ Known Limitations

- **Single-face input only.** The pipeline currently processes one detected face per image; multi-face images are not handled.
- **Search API dependency.** The reverse-image-search step relies on a third-party API (Google Cloud Vision / SerpAPI). Result quality, rate limits, and availability depend on that provider, not on this codebase.
- **No confidence threshold/config yet.** The face re-verification step reports a distance score, but there's no configurable confidence cutoff — matches are currently treated as verified based on a fixed internal comparison rather than a tunable threshold.
- **Testnet, not mainnet.** The contract is deployed to Polygon Amoy (a public testnet), not a production/mainnet chain. This is sufficient to demonstrate a real, verifiable on-chain record, but the record is not economically final the way a mainnet transaction would be.
- **Candidate ranking is basic.** When multiple candidates are returned by the search step, ranking/selection logic is simple and could surface a false positive if visually similar but different individuals appear in results.
- **No duplicate-submission protection.** Running the pipeline again on the same image will create a new on-chain record rather than detecting that one already exists.
- **Biometric data handling.** Face encodings and images are processed locally and referenced (via hash/CID) on-chain; no consent-management or data-retention system is implemented, since this is a hackathon demo rather than a production deployment.
- **English-centric search.** No specific handling for non-Latin-script social platforms or region-specific search engines.

## 🔒 Security & Privacy

The original face image is never written directly to the blockchain — only cryptographic hashes and references to the archived evidence are stored on-chain. Sensitive credentials (`.env`, `PRIVATE_KEY`, `PINATA_JWT`, `SERPAPI_KEY`) are excluded from version control.

For any real-world deployment beyond this hackathon demo, proper consent, privacy, data-retention, and legal review would be required before processing biometric data.

## 🚧 Future Improvements

- Support multiple faces in a single input image
- Configurable confidence-score thresholds for verification
- Improve candidate ranking and duplicate-record detection
- Add a web dashboard for browsing verification results
- Add QR-based blockchain verification
- Support additional EVM networks / mainnet deployment
- Add automated smart-contract tests
- Add encrypted evidence storage

## 👥 Team

**HH Goa 2026 — Face Identification Challenge**

- Tanmay Tripathi ([@Tanmay2006-Tech](https://github.com/Tanmay2006-Tech))
- Anandi Mahajan  ([@ghost33218](https://github.com/ghost33218))

## 📄 License

This project was created for the HH Goa 2026 hackathon challenge.
