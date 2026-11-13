# ChaptarrNG PR #190 primary localization review — W1100–W1149

## Exact scope and snapshot

This packet reviews zero-based positions 1100–1149 from `docs/localization/source-followup-20261101.json`: 50 source IDs × 12 direct locales = 600 cells. Sources include registered server errors and UI help, OAuth, accessibility, and scheduled-task labels. The English catalog, queue file, all locale catalogs, source registries, and caller files are pinned to exact Git blobs and SHA-256 values.

PR #190 remained open and draft on `codex/chaptarrng-localization-complete-20261031` at head `cc00a297fd221d52169f3c4683ffc1b0ee20871f`, tree `5987da199f6d5567803ba3ed6c4dd143d1263cdf`. Seven localization PRs were snapshotted before and after source selection and again at final seal. The worktree remained clean.

## Primary decisions

532 cells accept the current value; 57 corrections and 11 refinements are proposed; 0 cells are held. Proposals are review recommendations and were not applied. Notable findings address cross-format sync wording, the accessible dialog label, malformed/misleading OAuth errors, the `requestTokenSecret` missing-value message, and the expired OIDC session text. Exact product and protocol literals are checked per cell.

The W1050–W1099 `Dodge-ing` protected proper-name pun remains held across all 12 locales. Its primary and independent dispositions remain upheld, and all 12 applied values still match their pinned readbacks. This packet assigns no new disposition to that prior window.

## Structural and historical checks

All 600 final targets pass placeholder, markup, ICU signature, and source-registered protected-literal checks. Every source has an exact caller/display-path pin. Prior evidence checksums pass; the combined ledger contains all 13,200 prior cells through W1099. The already-recorded 195 historic final-hash differences remain unchanged since the prior packet. W1099 matches all 12 prior readbacks; W1150 is pinned as forward-boundary context only.

This is static machine-assisted primary review with moderate overall confidence. No qualified native-speaker approval, browser acceptance, or runtime validation is claimed. No tests, builds, scans, CI, or browser actions were run.

## Packet files

- `source-slice.jsonl`, `caller-context.jsonl`, `catalog-pins.json`, and `pinned-files.json`: exact source, caller, catalog, and file evidence.
- `review-cells.jsonl`, `correction-candidates.jsonl`, `refinement-candidates.jsonl`, `holds.jsonl`: all 600 decisions and exact target hashes.
- `protected-literal-integrity.jsonl`: placeholder, markup, ICU, and protected-token checks for each final target.
- `prior-dispositions-through-W1099.jsonl`, `prior-evidence-reattestation.json`, `w1099-backward-boundary.json`, `w1150-forward-boundary.json`: prior continuity and sequential boundaries.
- `snapshots/`, `summary.json`, `final-reattestation.json`, `manifest.json`, and `SHA256SUMS`: live PR state and packet seal.
