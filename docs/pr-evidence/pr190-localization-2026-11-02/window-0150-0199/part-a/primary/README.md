# ChaptarrNG PR #190 W150–199 primary semantic review — part A

- Live PR #190 is OPEN/DRAFT/CLEAN at `0117311b672af8d828fb45bad7e6026763b201da` / tree `a6500c8078f193af52555398525ec6f832241fd0`; the exact target worktree is clean.
- Scope: current missing-ID list positions 150–199 × 6 locales (`es`, `zh-Hans`, `hi`, `de`, `ja`, `fr`) = 300 cells.
- Source follow-up `docs/localization/source-followup-20261101.json` contains 1,210 unique IDs with list SHA-256 `a16dd0001c0a36f053bf0207060c338c428dc9beb2e3d929f7d73f19ad004e8c`. The 50 selected IDs exactly match current positions 150–199 and are disjoint from W0–149; prior packet source sets and checksums are recorded in `manifest.json`.
- Counts: 265 accept-current, 15 propose-refinement, 20 propose-correction, 0 holds. All 50 source IDs have caller evidence; 96 exact current caller references across 15 files were re-attested, including 34 line shifts. Current and recommended placeholders match; protected-literal mismatches: 0.
- Findings include the broken cookie warning in Spanish/Hindi/German, a Traditional Chinese string in the Simplified Chinese catalog, awkward IPTorrents RSS help across locales, correction of “Enable Deep Search” action wording, and provider/API terminology refinements. Exact target texts and hashes are in `review-cells.jsonl`.
- `locale-review-es-zh-Hans-hi-by-agent-a.jsonl` preserves the independent locale-reviewer output for es/zh-Hans/hi. de/ja/fr were reviewed in this task. Native-speaker approval is not claimed.
- This is part A; part B covers the remaining six locales separately. No repository/catalog edits, PR actions, tests, builds, scans, CI/workflows, releases, tags, or merges were performed.
