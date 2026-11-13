# ChaptarrNG PR #190 W300–349 primary semantic review

- Exact PR state: OPEN/DRAFT at `4b862646fbd038cfa4c16a94f7b6ac16f181751c` / tree `d76d887609ae90c9238ffda9b192a4c0c72be227`; source list contains 1,210 unique IDs and SHA-256 `a16dd0001c0a36f053bf0207060c338c428dc9beb2e3d929f7d73f19ad004e8c`.
- Scope: source-list positions 300–349 across all 12 direct locales = 50 source IDs / 600 current locale cells.
- Caller registry pins: 50 source IDs and 51 exact caller refs across 9 files; mismatches: 0.
- Dispositions: {'accept-current': 559, 'propose-correction': 9, 'propose-refinement': 32, 'hold': 0}. Correction/refinement candidates are in `correction-candidates.jsonl`; every cell with exact current text, hash, and rationale is in `review-cells.jsonl`. Source-specific caller rationales and the full candidate decisions are in `review-decisions.json`.
- Placeholder mismatches: 0; markup mismatches: 0; protected-literal mismatches in current targets: 3; candidate mismatches: 0.
- Final reattestation in `final-reattestation.json` reread the live PR head, all 600 source/target cells, and all caller refs without drift.
- Prior windows 0–299 have no same-source-ID disposition overlap with this slice (verified against all recorded primary/cross-review JSONL ledgers). `prior-context-dispositions.jsonl` records the adjacent W299 source disposition for continuity; `prior-disposition-boundary.json` records the scan and checksums.
- Agent/model semantic review only; native-speaker approval is not claimed. No repository/catalog/PR edits, tests, builds, scans, CI, browser actions, or workflow edits were performed.
