# ChaptarrNG PR #190 W250–W299 Core cross-review

This packet adjudicates all 600 cells across 50 English Core keys and 12 locales, pinned to PR head `2a9995a2bf63f06814bd8780736305f16bd6b33a` and tree `f6ae6530b73bf581c1fbc5a8c13eacd7342e9172`.

## Result

- Accept 558 current targets and recommend 42 target changes.
- Reconcile 33 primary proposals against 30 blind holds; 9 cells overlap.
- Add 9 changes for blind-only findings and refine 4 primary candidates using pinned caller or locale terminology evidence.
- Reject blind finding F011 for all 12 `Book` cells: the exact callers use this key as a book-title column, and every current translation is a direct book noun label, while the separate BookCount key names the number.
- Accept the six protected-literal scanner exceptions for `BackupIntervalHelpText`: each translation expands DB as “database” and retains Chaptarr.
- Keep native-speaker review outstanding for every cell. These are review recommendations, not native signoff.

## Pin and scope

Live filtered PR metadata at 2026-11-04T22:04:52Z–2026-11-04T22:04:56Z showed PR #190 open/draft, branch and pull refs at `2a9995a2bf63f06814bd8780736305f16bd6b33a`, and exact clean source worktree tree `f6ae6530b73bf581c1fbc5a8c13eacd7342e9172`. The API base is `17bde320915af42de73b8646ad56f8ba2ccebf4e` while live main is `9a44e91c96cd9f2eac1a351b1366f63c26b2ffc3` (26 commits ahead). The compare file list contains no Core English or target localization catalogs; review evidence remains pinned to the specified PR head/tree. No PR body was retrieved.

The blind reviewer disclosed only aggregate prior-window counts from the candidate-free verifier and sibling directory filenames from a top-level listing; it did not inspect prior translations, historical per-cell rows, or W250 primary results.

## Files

- `cross-review-cells.jsonl`: all 600 cell decisions, current and recommended target hashes, input-row hashes, caller links, and token checks.
- `selected-changes.jsonl`: the 42 proposed target changes.
- `caller-evidence.json`: deduplicated exact runtime translation callsites by source key.
- `decision-reconciliation.json`: finding-by-finding reconciliation, overlap, the rejected F011 claim, literal scanner exceptions, and blind reviewer disclosure.
- `review-selections.json`: the 13 cross-review target refinements/new targets and full adjudication map.
- `live-pr-attestation.json`, `base-drift-comparison.json`: filtered live refs and base/main file-list comparison.
- `build_cross_review.py`, `verify_cross_review.py`: deterministic packet builder and verifier.
- `manifest.json`, `SHA256SUMS.txt`: packet seal and checksums.

Verify from this directory with `sha256sum -c SHA256SUMS.txt` and `python3 verify_cross_review.py`. The verifier rechecks the three sealed input packets and this output’s exact source-worktree pin; it does not run product tests, builds, or CI.
