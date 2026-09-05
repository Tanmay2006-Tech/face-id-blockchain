# Face ID Blockchain

> **HH Goa 2026 — Task #3: Face Identification & Blockchain Verification**

An end-to-end face identification and verification pipeline that discovers potential matches across the web, re-verifies them using facial embeddings, archives the resulting evidence on IPFS, and creates a tamper-evident verification record on the Polygon Amoy blockchain.

---

## 🚀 Overview

The pipeline takes a face image as input and performs:

```text
Face Image
    │
    ▼
Face Detection & Encoding
    │
    ▼
Reverse Image Search
    │
    ▼
Candidate Images
    │
    ▼
Face Re-verification
    │
    ▼
Best Verified Match
    │
    ├──────────────► IPFS Evidence Archive
    │
    ▼
Tamper-Evident Blockchain Record
    │
    ▼
On-chain Verification
```

The system combines computer vision, reverse image search, decentralized storage, and blockchain verification into a single pipeline.

## ✨ Features

- 🧑‍💻 Face detection and facial embedding generation
- 🔍 Reverse image search for discovering potential matches
- 🧠 Facial embedding comparison to verify the same person rather than relying only on visual similarity
- 🌐 Web and social-media candidate discovery
- 📦 Complete match payload archived on IPFS
- ⛓️ Tamper-evident record stored on Polygon Amoy
- 🔐 SHA-256 hashing of face encoding and match payload
- ✅ Automatic verification of local data against the on-chain record
- 🧪 Dry-run mode for testing without blockchain submission

## 🏗️ Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Face Recognition | `face_recognition` / `dlib` |
| Reverse Image Search | Google Cloud Vision |
| Decentralized Storage | Pinata / IPFS |
| Blockchain | Polygon Amoy |
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

The reference image is submitted to the reverse-image-search component.

Potential matching pages/images are collected from the web and social platforms.

Example output:

```text
Social media matches found: 16
```

The results are treated as candidates, not as confirmed identity matches.

### 3. Face Re-verification

Each candidate image is downloaded and analyzed.

The candidate's facial embedding is compared with the original face embedding. A lower face distance indicates a closer facial embedding match.

Example:

```text
Face verification results

Distance: 0.0000
Verified match: YES
```

This additional verification step prevents the system from trusting reverse-image-search results alone.

### 4. IPFS Evidence Archive

Once a verified match is selected, the complete match payload is uploaded to IPFS through Pinata. The IPFS CID provides a content-addressed reference to the archived evidence.

Example:

```text
Pinned to IPFS:
QmX6ghcqhvw0jUtCYRsrL1CBxXaRPTN2FvwZhw1QdbevCH
```

The IPFS gateway can be used to inspect the archived payload:

`https://gateway.pinata.cloud/ipfs/QmX6ghcqhvw0jUtCYRsrL1CBxXaRPTN2FvwZhw1QdbevCH`

### 5. Blockchain Verification

The project uses a Solidity smart contract deployed on Polygon Amoy.

- **Contract:** `0xEE30E6f46A892bd222DFa43BbE34c86C3042f188`
- **Network:** Polygon Amoy (Chain ID: `80002`)

The blockchain record contains cryptographic references rather than storing the original face image directly on-chain. The contract records:

- Face encoding SHA-256
- Match payload SHA-256
- Matched URL
- Reverse-search source
- IPFS CID
- Face-match distance
- Timestamp
- Submitting wallet address

### 6. End-to-End Verification

After submitting the blockchain transaction, `verify_record.py` reads the record back from the smart contract and compares it with the local payload.

Successful execution produces:

```text
✓ On-chain record written
✓ VERIFIED — record #0 on-chain matches the local payload exactly.
```

This provides an end-to-end verification path from the original face scan to the blockchain record.

## 🔐 Tamper-Evident Design

The system generates two important hashes — `SHA-256(face encoding)` and `SHA-256(canonical match payload)` — which are recorded on-chain. The complete payload itself is stored on IPFS.

```text
Local Face Encoding ──▶ SHA-256 ──▶ Blockchain Record
Match Payload       ──▶ SHA-256 ──▶ Blockchain Record
Match Payload       ──▶ IPFS ──▶ CID ──▶ Blockchain Record
```

If the local payload is modified after submission, its calculated hash will no longer match the hash stored on-chain.

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

## 🏃 Running the Pipeline

Place an input image in the project directory and run:

```bash
python src/pipeline.py test_face.jpg
```

The pipeline will perform:

```text
STEP 1 - Face detection + encoding
STEP 2 - Reverse-image search
STEP 3 - Face re-verification
STEP 4 - IPFS pin
STEP 5 - Polygon Amoy blockchain write
STEP 6 - On-chain re-verification
```

### 🧪 Dry Run

To test the complete pipeline without writing to the blockchain:

```bash
python src/pipeline.py test_face.jpg --dry-run-chain
```

To skip IPFS:

```bash
python src/pipeline.py test_face.jpg --no-ipfs
```

## 📜 Smart Contract

`FaceRecord.sol` provides functions for:

- `addRecord(...)`
- `getRecord(...)`
- `totalRecords()`

Each submitted record receives a sequential record ID. The `RecordAdded` event provides an auditable blockchain event containing the record information.

### Working with Hardhat

- Deploy: `scripts/deploy.ts`
- Send a raw op transaction: `scripts/send-op-tx.ts`
- Sample tests: `test/Counter.ts`
- TypeChain bindings for the contracts live in `types/ethers-contracts/`

## 🌐 Blockchain Transaction

A successful demonstration transaction on Polygon Amoy:

```text
Transaction:
98b9ec3e8a1239ac188373460ec55080cb842ada98e9363421e1ce3a1c23f23d

Block:
46797023
```

View the transaction on PolygonScan:

`https://amoy.polygonscan.com/tx/98b9ec3e8a1239ac188373460ec55080cb842ada98e9363421e1ce3a1c23f23d`

## 🎯 Hackathon Requirement Mapping

| HH Goa Task Requirement | Implementation |
|---|---|
| Face detection | `face_encode.py` |
| Face encoding | `face_recognition` / `dlib` |
| Web/social media search | `reverse_search.py` |
| Matching face verification | `face_verify.py` |
| Blockchain verification | `blockchain_writer.py` |
| Decentralized storage | Pinata / IPFS |
| Tamper-evident record | SHA-256 + Polygon Amoy |
| On-chain re-verification | `verify_record.py` |
| End-to-end pipeline | `pipeline.py` |

## 🔒 Security & Privacy

The project is designed to avoid putting the original face image directly on the blockchain. Instead, the blockchain stores cryptographic hashes and references to the associated evidence.

Sensitive credentials such as `.env`, `PRIVATE_KEY`, `PINATA_JWT`, and `SERPAPI_KEY` must never be committed to the repository.

For real-world deployment, appropriate consent, privacy, data-retention, and legal requirements should be considered before processing biometric data.

## 🚧 Future Improvements

- Support multiple faces in a single input image
- Improve candidate ranking
- Add a web dashboard for verification results
- Add QR-based blockchain verification
- Support additional EVM networks
- Add automated smart-contract tests
- Add encrypted evidence storage
- Add stronger duplicate/candidate filtering
- Add confidence scoring and configurable verification thresholds

## 👥 Team

**HH Goa 2026 — Face Identification Challenge**

Team:
- Tanmay Tripathi ([@Tanmay2006-Tech](https://github.com/Tanmay2006-Tech))
- `<Team Member 2>`
- `<Team Member 3>`
- `<Team Member 4>`

## 📄 License

This project was created for the HH Goa 2026 hackathon challenge.

---

### ✅ Before you push

- Replace the `<Team Member N>` placeholders above with your actual teammates.
- Double-check `.env`, API keys, and the private key are **not** in the repo or in this README.
- Consider adding a screenshots/demo section showing the 6 pipeline steps and the successful Polygon transaction for judges.
