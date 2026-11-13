# ChaptarrNG PR #190 W400–449 primary semantic review

- Exact PR state: OPEN/DRAFT at `2eb0ae6eb15ebc366eea44dd969265c0f6366445` / tree `1340ba7d0642217aa81e3789e908931bd6fa74f1`; source list contains 1,210 unique IDs and SHA-256 `a16dd0001c0a36f053bf0207060c338c428dc9beb2e3d929f7d73f19ad004e8c`.
- Scope: source-list positions 400–449 across all 12 direct locales = 50 source IDs / 600 current locale cells.
- Caller pins: 49 source IDs and 90 exact production C# references across 27 files; mismatches: 0; caller gaps: 1.
- Dispositions: {'accept-current': 500, 'propose-correction': 43, 'propose-refinement': 45, 'hold': 12}. Correction/refinement candidates are in `correction-candidates.jsonl`; every cell with exact current text, hash, and rationale is in `review-cells.jsonl`. Source-specific caller rationales and the full candidate decisions are in `review-decisions.json`.
- Placeholder mismatches: 0; markup mismatches: 0; protected-literal mismatches in current targets: 0; candidate mismatches: 0.
- Final reattestation in `final-reattestation.json` reread the live PR head, all 600 source/target cells, and all caller refs without drift.
- Prior windows 0–399 have no same-source-ID disposition overlap with this slice (verified against all recorded primary/cross-review JSONL ledgers). `prior-context-dispositions.jsonl` reattests the adjacent W399 source dispositions against live targets and callers; `prior-disposition-boundary.json` records the scan and checksums.
- Agent/model semantic review only; native-speaker approval is not claimed. No repository/catalog/PR edits, tests, builds, scans, CI, browser actions, or workflow edits were performed.
