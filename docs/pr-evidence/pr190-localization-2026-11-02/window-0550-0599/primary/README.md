# ChaptarrNG PR #190 W550–599 primary semantic review

- Exact PR state: OPEN/DRAFT at `015ff68d96340292b5e6a45d34496a5936ebf09c` / tree `bbb59a14a50a4b63bc209663c1e4b873ead4fc10`.
- Scope: source-list positions 550–599 across 12 locales = 50 source IDs / 600 current locale cells.
- Exact source inventory: `source-slice.jsonl`; source-list SHA-256 `a16dd0001c0a36f053bf0207060c338c428dc9beb2e3d929f7d73f19ad004e8c`.
- Production caller pins: 50 of 50 source IDs, 69 exact C# references across 42 files; gaps and mismatches: 0.
- Dispositions: {'accept-current': 329, 'propose-correction': 240, 'propose-refinement': 31, 'hold': 0}. Every cell has exact source/current-target hashes and caller context in `review-cells.jsonl`; recommendations are in `correction-candidates.jsonl`.
- Placeholder mismatches: 0; markup mismatches: 0; current protected-literal mismatch cells: 0; proposed protected-literal mismatches: 0.
- W549 adjacent context: source hash was reattested; 8 of 12 previous current targets still match, while 4 prior recommendations match the live targets after the apply commit. All 12 live target hashes and caller refs are recorded.
- Earlier ledger overlap: 0 source IDs.
- Primary model review only; native-speaker approval is not claimed. No repository/catalog/PR edits, tests, builds, scans, CI, browser actions, or workflow edits were performed.

See `summary.json`, `manifest.json`, and `SHA256SUMS` for packet inventory and integrity.
