# ChaptarrNG PR #190 W950–999 application

This application is pinned to PR #190 head `961d3102ad3098ee188a6c87a0c88eea5f5ab332` and tree `c46078c93545042313aa1b35bc3b283b1f3b5406` at the start of the change.

The frozen input covers 50 source strings × 12 locales (600 cells). Primary review, independent cross-review, and third-party adjudication approve 23 catalog target changes. The exact-hash plan records each source-text hash, previous target value and hash, final value and hash, target file, and adjudicated disposition. One separate Indonesian Farsi cell remains unchanged and held for native-speaker review.

The 600-cell readback confirms each resulting target against the catalog. The review also confirms that all 12 catalogs parse, key sets and order are preserved, and only the 23 approved target values changed. This is machine review; qualified native-speaker approval is still pending. No tests, builds, scans, CI, or browser review were run for this window.

## Files

- `exact-hash-apply-plan.jsonl` — the 23 approved target changes, pinned to source and target hashes.
- `exact-hash-readback.json` — catalog/key-order and scope verification summary.
- `full-window-readback.jsonl` — resulting values for all 600 reviewed cells, including the held cell.
- `SHA256SUMS` — checksums for this packet and this README.
