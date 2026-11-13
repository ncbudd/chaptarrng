# ChaptarrNG W550–599 exact-hash application

Applied the independently reviewed final targets for source ordinals 550–599 at PR #190 head `015ff68d96340292b5e6a45d34496a5936ebf09c` (tree `bbb59a14a50a4b63bc209663c1e4b873ead4fc10`).

## Review outcome

The primary and independent cross-review cover 600 cells across 50 source IDs and 12 locales. They reattested 69 caller references across 42 files and found no placeholder, markup, protected-literal, or exact-hash mismatches.

The final reviewed disposition is 322 accept-current, 233 corrections, 33 refinements, and 12 holds. Applied 266 exact-hash target updates across the 12 locale catalogs. Source ordinal 561 remains held across all locales because the English source says “less than 25000” while the caller accepts 25000 and rejects only values above it. The source wording and those 12 translations remain unchanged pending a source wording decision.

## Files

- `primary/`: checksummed primary review packet.
- `crossreview/`: checksummed independent cross-review and final 600-cell ledger.
- `application/apply_exact_hash.py`: exact-head and exact-current-hash guarded applier.
- `application/apply-plan.jsonl`: the 266 approved changes with expected old and new hashes.
- `application/held-cells.jsonl`: the 12 held ordinal-561 cells.
- `application/readback.json`: catalog counts and post-write readback summary.

All 12 target catalogs retain 4,165 keys. Catalog key parity and placeholder parity were checked after application. No tests, builds, scans, CI jobs, browser review, workflow changes, releases, tags, or merges were performed. Machine review is not qualified native-speaker approval; native-speaker and current-head browser review remain outstanding.
