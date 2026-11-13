# ChaptarrNG PR #190 W200–249 independent cross-review

- Reattested PR state: OPEN/DRAFT at `32686f13760d04de2bba00af47fc561e632741de`, tree `13de6a00cb6eb7206523f000d6ef345084f3c78e`.
- Frozen scope: source-list positions 200–249 across all 12 direct locales; 50 source IDs and 600 current target cells.
- Cross-review: 599 cells accepted and one refined. Of 52 primary correction/refinement proposals, 51 are accepted as proposed and one Hindi punctuation candidate is refined. No candidate was rejected, held, or missed, and no additional current-cell issue was found.
- The Hindi candidate for source ordinal 200 used U+3002 `。`; the cross-reviewed value uses Hindi danda U+0964 `।`. See `additional-findings.jsonl` for exact values and SHA-256 hashes.
- Reattested all 600 current values and 52 caller-reference records. Caller evidence covers 32 unique exact source lines in 7 files. Source and target catalog hashes, caller pins, and the zero-mismatch counts are in `reattestation.json`.
- Placeholder, markup, protected-literal, and localized UI term checks passed. Per-cell decisions and their exact source/current/final hashes are in `cross-review-cells.jsonl`; check results are in `protected-literal-placeholder-checks.jsonl`.
- Primary input packet: `/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0200-0249-primary-20261102`. The reviewed input and primary-decision checksums are embedded in `reattestation.json` and `summary.json`.
- This is an independent semantic cross-review, not native-speaker approval. No repository or PR changes, tests, builds, scans, CI, browser actions, workflow changes, releases, tags, or merges were made.
- `build_cross_review.py` records the packet-generation and live reattestation procedure. `SHA256SUMS` covers this packet’s files other than itself.
