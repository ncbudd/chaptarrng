# ChaptarrNG PR #190 W0–49 independent cross-review

This packet cross-reviews the 600 cells for the first 50 `currentMissingIds` at PR head `7bb2b2f977e81d214318b3f873afe8ab17f03ed5` / tree `5fdb46e8b55083b44f6ca109b1e46fd5b375b7cb`. The live PR was still open and draft at that head during the final check. The exact-head audit worktree was clean. No repository or PR files were edited.

## Result

- 600 cells across 12 locales and 50 source IDs were independently cross-reviewed.
- Primary candidates: 65 across 20 IDs. **63 accepted**, **2 refined**.
- Primary keep rows: 535. **510 accepted unchanged**, **25 missed corrections**.
- Cross-review dispositions: **573 accepted**, **2 refined**, **25 missed**, **0 held**, **0 no-op**.
- Every recommended replacement has its exact UTF-8 text and SHA-256 in `crossreview-decisions.jsonl`. The ledger also preserves each source, current value/hash, primary candidate/hash, source caller refs, primary verdict, review head/tree, and exact action.

## Re-attestation and evidence

`attestation.json` records exact source/current/candidate hash checks, all 12 catalog file hashes, packet checksums, prior-overlap checks, and the metadata issue below. `caller-pins.jsonl` includes all 134 unique provider ID-to-caller references with current line, unique exact line text, full line hash, file hash, and registry reference. The primary registry’s stored coordinates shifted for 86 references; all were found uniquely at their current locations.

`locale-a/` and `locale-b/` retain the two locale-subset ledgers and their own verified checksums. The root `SHA256SUMS` covers the full packet, including both subpackets.

The input-cell packet leaves `placeholderTokens` empty for seven IDs (84 locale rows), while the semantic packet records file extensions and bracket literals as protected values. The listed values are present in each English source, current target, and recommended candidate; no literal loss or source/current hash mismatch was found. This is a metadata-scope difference and is called out in `attestation.json`. No W0–49 cell overlaps the 101-cell exact-head reconciliation or all 22 recursive `docs/localization` JSON evidence files.

This is an agent semantic cross-review, not qualified native-speaker approval. Native-speaker approval and exact-current-head headed browser acceptance remain false. No tests, builds, scans, CI, releases, tags, or merges were run as part of this review.
