# ChaptarrNG PR #190 W350–399 primary semantic review

- Exact PR state: OPEN/DRAFT at `e9de5ac22aba7780f4ff55b3fd903731fea89269` / tree `1c8212fcc3623723b306865ac4d7f765ecf72a22`; source list contains 1,210 unique IDs and SHA-256 `a16dd0001c0a36f053bf0207060c338c428dc9beb2e3d929f7d73f19ad004e8c`.
- Scope: source-list positions 350–399 across all 12 direct locales = 50 source IDs / 600 current locale cells.
- Caller pins: 50 source IDs and 64 exact caller refs across 28 files (including direct notification callsites); mismatches: 0.
- Dispositions: {'accept-current': 528, 'propose-refinement': 59, 'propose-correction': 13, 'hold': 0}. Correction/refinement candidates are in `correction-candidates.jsonl`; every cell with exact current text, hash, and rationale is in `review-cells.jsonl`. Source-specific caller rationales and the full candidate decisions are in `review-decisions.json`.
- Placeholder mismatches: 0; markup mismatches: 0; protected-literal mismatches in current targets: 0; candidate mismatches: 0.
- Final reattestation in `final-reattestation.json` reread the live PR head, all 600 source/target cells, and all caller refs without drift.
- Prior windows 0–349 have no same-source-ID disposition overlap with this slice (verified against all recorded primary/cross-review JSONL ledgers). `prior-context-dispositions.jsonl` reattests the adjacent W349 source dispositions against live targets and callers; `prior-disposition-boundary.json` records the scan and checksums.
- Agent/model semantic review only; native-speaker approval is not claimed. No repository/catalog/PR edits, tests, builds, scans, CI, browser actions, or workflow edits were performed.
