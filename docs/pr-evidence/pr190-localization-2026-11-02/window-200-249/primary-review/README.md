# ChaptarrNG PR #190 W200–249 primary semantic review

- Exact PR state: OPEN/DRAFT at `32686f13760d04de2bba00af47fc561e632741de` / tree `13de6a00cb6eb7206523f000d6ef345084f3c78e`; source list contains 1,210 unique IDs and SHA-256 `a16dd0001c0a36f053bf0207060c338c428dc9beb2e3d929f7d73f19ad004e8c`.
- Scope: source-list positions 200–249 across all 12 direct locales = 50 source IDs / 600 current locale cells.
- Caller registry pins: 50 source IDs and 52 exact caller refs across 7 files; mismatches: 0.
- Dispositions: {'propose-correction': 40, 'propose-refinement': 12, 'accept-current': 548, 'hold': 0}. Correction/refinement candidates are in `correction-candidates.jsonl`; every cell with exact current text and hash is in `review-cells.jsonl`.
- Placeholder mismatches: 0; markup mismatches: 0; protected-literal mismatches in current targets: 0; candidate mismatches: 0.
- Final reattestation in `final-reattestation.json` reread the live PR head, all 600 source/target cells, and all caller refs without drift.
- Prior windows 0–199 have no same-source-ID disposition overlap with this slice (verified against all recorded primary/cross-review JSONL ledgers). `prior-context-dispositions.jsonl` records the adjacent W199 label disposition that frames W200’s hidden ABS help field; `prior-disposition-boundary.json` records the scan and checksums.
- Agent/model semantic review only; native-speaker approval is not claimed. No repository/catalog/PR edits, tests, builds, scans, CI, browser actions, or workflow edits were performed.
