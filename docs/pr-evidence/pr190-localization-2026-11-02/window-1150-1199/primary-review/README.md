# ChaptarrNG PR #190 primary localization review — W1150–W1199

## Exact scope and snapshot

This packet reviews zero-based positions 1150–1199 from `docs/localization/source-followup-20261101.json`: 50 source IDs × 12 locales = 600 cells. All source IDs are server-message entries. Inputs bind the English source, all locale catalogs, source registry, caller index, and exact production callers to hashes and Git blobs.

PR #190 is OPEN/DRAFT on `codex/chaptarrng-localization-complete-20261031` at head `6e7a5341b7ccac31d950c73db68277f9a1f18f8e`, tree `d073e1373021bf715db37461a12654f7e993cdbf`. The official remote branch, PR, and clean local worktree were reattested at seal. ChaptarrNG did not move during this review. Snapshots include all seven localization PRs; SeerrNG moved independently during the window and is recorded in `final-reattestation.json`.

## Primary decisions

409 cells accept current values, 133 corrections and 46 refinements are proposed, and 12 cells are held. The proposals are recommendations only; no catalog or PR edits were made.

The sole held source is W1187 `server.message.md764ed5e74b4` (“{value0} conversion was cancelled.”), held in all 12 locales. Both callers pass `TargetQualityName ?? "M4B"`, while the source registry marks `M4B` as a protected literal. The value can be another configured quality. Eleven current locale targets omit the fixed literal; German includes `M4B` but can still disagree with the dynamic value. Do not insert or infer a fixed M4B label until the source/registry conflict is resolved.

Notable proposals correct parser-versus-identification wording, M4B conversion failure grammar and file-versus-conversion subjects, “finalizing” status aspect, file-import terminology, FFmpeg availability, and exit-code sentence order. Exact protected product/tool literals and dynamic placeholders are checked per cell.

## Structural and historical checks

- 59 exact caller references across seven caller files; zero caller gaps.
- Placeholder, markup, and ICU parity pass for all 600 final targets.
- There are no new unheld protected-literal failures. W1187’s protected-literal conflict is explicit and held in all locales; 11 current rows lack `M4B`, while one contains it but remains semantically unsafe for the dynamic caller value.
- Prior dispositions through W1149 reattest 13,800 cells with zero current-value drift. The 195 recorded historic final-versus-current differences remain stable; the 12 W1050 `Dodge-ing` holds remain preserved.
- W1149 backward boundary: 12/12 match applied readback. W1150 forward context matches all 12 prior readbacks. W1200 is context-only.

This is static machine-assisted primary review with moderate overall confidence. It does not claim native-speaker approval, headed browser acceptance, or runtime validation. No tests, builds, scans, CI, or browser actions were run.

## Packet contents

- Frozen source/caller/catalog inputs and exact-head snapshots: `source-slice.jsonl`, `caller-context.jsonl`, `input-cells.jsonl`, `catalog-pins.json`, `pinned-files.json`, `source-selection.json`, and `snapshots/`.
- Full 600-cell ledger and derived proposals: `review-cells.jsonl`, `correction-candidates.jsonl`, `refinement-candidates.jsonl`, `holds.jsonl`, `protected-literal-integrity.jsonl`.
- Review partitions: `locale-review-ar-de-es-fr-hi-id.jsonl` and `locale-review-ja-ko-pt-vi-zh.jsonl`, with sidecar SHA-256 files and `review-parts-manifest.json`.
- Continuity evidence: `prior-disposition-reattestation.jsonl`, `prior-window-reattestation.json`, `w1149-backward-boundary.json`, and `w1200-forward-boundary.json`.
- Seal evidence: `summary.json`, `final-reattestation.json`, `snapshots/final-seal-all-pr-heads.json`, `manifest.json`, and `SHA256SUMS`. `INPUT-SHA256SUMS` verifies the frozen input bundle.
