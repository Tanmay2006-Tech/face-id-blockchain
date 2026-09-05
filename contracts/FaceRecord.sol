// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title FaceRecord
/// @notice Stores tamper-evident records linking a face-encoding hash to
///         a reverse-image-search match. We store the SHA-256 hash of
///         the face encoding (never the raw biometric vector) plus a
///         hash of the full match payload, alongside the matched URL
///         for human readability. Anyone can verify a record by
///         recomputing the payload hash off-chain and comparing it to
///         what's stored here — the chain guarantees the record hasn't
///         been altered since it was written.
contract FaceRecord {
    struct Record {
        bytes32 faceEncodingHash;   // sha256 of the 128-d face encoding
        bytes32 matchPayloadHash;   // sha256 of the full JSON match payload
        string matchedUrl;          // the social media URL that was matched
        string matchSourceApi;      // e.g. "google-cloud-vision-web-detection"
        string ipfsCid;             // IPFS CID of the full payload ("" if not pinned)
        uint256 faceMatchDistance;  // face-embedding distance * 1e6 (0 = not verified)
        uint256 timestamp;          // block timestamp at write time
        address submittedBy;        // wallet that wrote the record
    }

    Record[] private records;

    event RecordAdded(
        uint256 indexed recordId,
        bytes32 indexed faceEncodingHash,
        string matchedUrl,
        string ipfsCid,
        uint256 timestamp
    );

    /// @notice Add a new tamper-evident record.
    /// @param faceMatchDistanceScaled the face_recognition embedding
    ///        distance between source face and matched candidate face,
    ///        scaled by 1e6 to avoid floats on-chain (e.g. 0.42 -> 420000).
    ///        Pass 0 if no independent face re-verification was performed.
    function addRecord(
        bytes32 faceEncodingHash,
        bytes32 matchPayloadHash,
        string calldata matchedUrl,
        string calldata matchSourceApi,
        string calldata ipfsCid,
        uint256 faceMatchDistanceScaled
    ) external returns (uint256 recordId) {
        records.push(
            Record({
                faceEncodingHash: faceEncodingHash,
                matchPayloadHash: matchPayloadHash,
                matchedUrl: matchedUrl,
                matchSourceApi: matchSourceApi,
                ipfsCid: ipfsCid,
                faceMatchDistance: faceMatchDistanceScaled,
                timestamp: block.timestamp,
                submittedBy: msg.sender
            })
        );
        recordId = records.length - 1;
        emit RecordAdded(recordId, faceEncodingHash, matchedUrl, ipfsCid, block.timestamp);
    }

    function getRecord(uint256 recordId) external view returns (Record memory) {
        return records[recordId];
    }

    function totalRecords() external view returns (uint256) {
        return records.length;
    }
}
