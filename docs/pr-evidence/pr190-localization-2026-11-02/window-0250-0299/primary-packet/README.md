# ChaptarrNG PR #190 W250–299 primary semantic review

- Exact PR state: OPEN/DRAFT at `46a6abd437c78fafcec73f93f79944b5f84d3a39` / tree `90a59b1c329feeb3fb34bdc5050128c8792b573e`; source list contains 1,210 unique IDs and SHA-256 `a16dd0001c0a36f053bf0207060c338c428dc9beb2e3d929f7d73f19ad004e8c`.
- Scope: source-list positions 250–299 across all 12 direct locales = 50 source IDs / 600 current locale cells.
- Caller registry pins: 50 source IDs and 59 exact caller refs across 14 files; mismatches: 0.
- Dispositions: {'accept-current': 533, 'propose-correction': 35, 'propose-refinement': 32, 'hold': 0}. Correction/refinement candidates are in `correction-candidates.jsonl`; every cell with exact current text, hash, and rationale is in `review-cells.jsonl`. Source-specific caller rationales and the full candidate decisions are in `review-decisions.json`.
- Placeholder mismatches: 0; markup mismatches: 0; protected-literal mismatches in current targets: 0; candidate mismatches: 0.
- Final reattestation in `final-reattestation.json` reread the live PR head, all 600 source/target cells, and all caller refs without drift.
- Prior windows 0–249 have no same-source-ID disposition overlap with this slice (verified against all recorded primary/cross-review JSONL ledgers). `prior-context-dispositions.jsonl` records the adjacent W249 source disposition for continuity; `prior-disposition-boundary.json` records the scan and checksums.
- Agent/model semantic review only; native-speaker approval is not claimed. No repository/catalog/PR edits, tests, builds, scans, CI, browser actions, or workflow edits were performed.
