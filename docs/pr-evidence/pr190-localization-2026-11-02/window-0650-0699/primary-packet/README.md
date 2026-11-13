# ChaptarrNG PR #190 W650–699 primary semantic review

- Exact PR state: OPEN/DRAFT at `4701933a50d367406fd6749c4baaf4befee22129` / tree `2b22ea480c934d2dc41c6813b1296f1a3c41b027`.
- Scope: source-list positions 650–699 across 12 locales = 50 source IDs / 600 current locale cells.
- Exact source inventory: `source-slice.jsonl`; source-list SHA-256 `a16dd0001c0a36f053bf0207060c338c428dc9beb2e3d929f7d73f19ad004e8c`.
- Production caller pins: 50 of 50 source IDs, 59 exact C# source-ID/template references across 48 files; gaps and mismatches: 0.
- Dispositions: {'accept-current': 501, 'propose-correction': 99, 'propose-refinement': 0, 'hold': 0}. Every cell has exact source/current-target hashes and caller context in `review-cells.jsonl`; recommendations are in `correction-candidates.jsonl`.
- Placeholder mismatches: 0; markup mismatches: 0; current protected-literal mismatch cells: 12; proposed protected-literal mismatches: 0.
- W649 adjacent context: source hash was reattested; all 12 live targets match the prior cross-review final targets after the apply commit; 4 original primary current targets remain unchanged and 8 primary recommendations match the live targets. W650 source/current-target strings and caller pins were reattested against the previous boundary; all 12 target values match, while 12 locale catalog file hashes changed with the apply commit.
- Earlier ledger overlap: 0 source IDs.
- Primary model review only; native-speaker approval is not claimed. No repository/catalog/PR edits, tests, builds, scans, CI, browser actions, or workflow edits were performed.

See `summary.json`, `manifest.json`, and `SHA256SUMS` for packet inventory and integrity.
