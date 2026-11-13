# ChaptarrNG PR #190 W200–W249 cross-review

This packet records an independent adjudication of the primary and blind reviews for 50 localization source IDs across 12 direct locales (600 cells), pinned to PR head `dc91bdcdf60ba422bb176cc7c58b9b1cab27facd` and tree `ffae435c871360ba958098bc0398a1f251f8b1e8`.

## Recommendation

- Keep 489 current targets.
- Recommend 99 target changes, drawing from 96 primary proposal cells and 34 blind proposal cells with 31 overlapping cells. The detailed choices and rationales are in `selected-changes.jsonl` and `cross-review-cells.jsonl`.
- Keep the 12 `AuthorsLabel` cells as text-free holds because the pinned caller audit found zero source references. No source, target, or candidate wording is included for those cells.
- Treat every recommendation as pending native-speaker review. This is a machine cross-review, not native-speaker signoff.
- Recommendations only: no catalog, source, test, workflow, or PR changes were made; no tests, builds, or CI were run.

The cross-review consulted caller context and exact-hash lineage for every proposal. It selected a review candidate or recorded a cross-review refinement where both candidate phrasings needed adjustment. The files include per-cell source/current/recommended target hashes, candidate-free and review row hashes, token inventories, and decision rationales. `review-selections.json` contains the complete proposal-cell adjudication map.

## Pinned inputs

- Candidate-free source: `/home/keith/Documents/code/task-scratch/chaptarrng-pr190-w200-249-primary-20261104/candidate-free/input/`. Its manifest SHA-256 is `089ce6eb329a24793ba0410fa9d007487b6dd4d9161ba1b6ef1f0cd7597c9beb`; its cell file SHA-256 is `3a66a04f548e10d73cf8c2f57acdf54b6a8888929dd691aed431fa50dbe046fb`.
- Primary packet: `/home/keith/Documents/code/task-scratch/chaptarrng-pr190-w200-249-primary-20261104/primary-review/`. Its sealed verifier passed for 600 cells, 96 proposals, and 12 text-free holds.
- Blind packet: `/home/keith/Documents/code/task-scratch/chaptarrng-pr190-w200-249-blind-20261104/`. Its sealed verifier passed for 600 cells, 34 proposals, and 12 hash-only holds.
- The candidate-free, primary, and blind packet verifiers all confirmed the same exact head/tree; the source worktree was clean.

## Live base drift

At `2026-11-04T16:16:28Z`, PR #190 remained open and draft. Its API base was `17bde320915af42de73b8646ad56f8ba2ccebf4e`; live `main` was `dbbb46abf8bee2f88e5a8a6ca7d8e141bf4d15a2`. The GitHub compare API reported eight commits from that API base to live `main`, with changes limited to workflows, `AGENTS.md`, retirement documentation, and runner-policy scripts; it reported no localization source or catalog changes. `base-drift-comparison.json` records the exact changed-file list. This is a point-in-time reattestation; recheck the live PR and refs before applying any recommendation.

## Files

- `cross-review-cells.jsonl`: one adjudication per source-locale cell.
- `selected-changes.jsonl`: 99 proposed target changes only.
- `review-selections.json`: proposal selections and rationales.
- `live-pr-attestation.json`, `base-drift-comparison.json`: exact pinned refs and base/main comparison.
- `verify_cross_review.py`: deterministic output, lineage, token, hold, and packet checksum verifier.
- `build_cross_review.py`: deterministic packet builder from the sealed candidate-free, primary, and blind inputs.
- `SHA256SUMS.txt`: checksums for every other packet file.

Verify the packet checksums with `sha256sum -c SHA256SUMS.txt`, then run:

```sh
python3 verify_cross_review.py
```

The verifier also reruns the three sealed input verifiers. It does not run tests, builds, or CI.
