# ChaptarrNG PR #190 semantic review cross-audit

This cross-audit compares the sealed primary ledger, sealed blind ledger, and candidate-free input packet. It covers all 31 selected cells. The audit checked packet/output checksums, manifest membership and hashes, source/current/recommended text hashes, locale catalog pins, caller snapshots and line hashes, corrected-source evidence, placeholder/protected-literal checks, and exact head/tree pins.

## Files

- `cross-audit-ledger.jsonl`: per-cell disposition, confidence, recommended text/hash comparison, and pin/structure checks.
- `report.md`: result and the one confidence variance.
- `SHA256SUMS`: hashes for the ledger and report.

The two ledgers agree on accept-current for every cell and on each exact recommended target. Confidence differs for zh-Hant `notification.heading.renamed` only; see the report.
