# ChaptarrNG PR #190 exact-head catalog coverage audit

Read-only audit at `580538d38f92e0ec005366ff6bea3f2634400c2e` (tree `b61f7ca1f5b496c01a32ba7b8f3520076ec5cfc1`), live open draft PR #190, base `03274100af783fdffaca4dd8436e163dc6b18795`. Exact worktree was clean.

## Catalog and source coverage

- 12 direct catalogs, 4165 English keys each, 1210 current source IDs, 14520 source/locale cells.
- Key sets match English in all catalogs. Nonblank string values: 0 failures. Placeholder token mismatches: 0.
- Locale ordered-key arrays form 2 sequences; they are not identical to English. Exact groups and the index of `EmbyJellyfinHostHelpText` are in `catalog-and-pin-attestation.json`. Existing-key order matches each locale's PR-base order, so the sequence differences predate this PR.
- Candidate-free coverage ledger has 14520 rows; rows retain source/current-target hashes and exact review evidence paths, never target text. Missing exact-current-source primary rows: 24 (source positions 654 and 695; their correction packets separately pin the current source and callers). Missing current-target hash evidence: 0.
- 11 existing translated cells differ from the PR base: 4 have retained exact-target-hash evidence, 7 do not. The uncovered cells are listed by ID/locale and hashes only in `changed-existing-cell-audit.jsonl`.
- Active unresolved holds: 61 cells across 9 IDs. See `active-holds.jsonl`; W1187's earlier primary hold is superseded by its dedicated final adjudication.

## Caller and runtime findings

Caller references are mapped hash-only in `caller-coverage.jsonl`, with current file/line status. The locale catalog loader merges English, then optional fallback, then the selected locale catalog. Since all direct catalogs have complete English key coverage, fallback is not needed for these 12 locales.

At the earlier PR head `edbfa7c`, `frontend/src/login.html` omitted `ar` from its RTL list and assigned Arabic LTR. The shared helper returns RTL for `ar`, and the registry marks Arabic as selectable/RTL. The current PR head fixes this with the one-line `ar` addition in commit `46049fad`; the resulting branch matches the helper for Arabic. A shared/generated direction source is a future drift-prevention improvement.

## Retained files

- `candidate-free-source-queue.jsonl`
- `candidate-free-coverage-map.jsonl`
- `changed-existing-cell-audit.jsonl`
- `active-holds.jsonl`
- `caller-coverage.jsonl`
- `catalog-and-pin-attestation.json`
- `build_audit.py`

The audit did not modify repository or PR files and did not run tests, builds, scans, or CI. Machine review evidence is not native-speaker approval.
