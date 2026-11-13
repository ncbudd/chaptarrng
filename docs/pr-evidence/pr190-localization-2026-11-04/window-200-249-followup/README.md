# ChaptarrNG PR #190 W200–W249 cross-review follow-up

This follow-up re-reviewed and applied the W200–W249 catalog window at source head `dc91bdcdf60ba422bb176cc7c58b9b1cab27facd` / tree `ffae435c871360ba958098bc0398a1f251f8b1e8`. The earlier application of 52 changes at head `32686f13760d04de2bba00af47fc561e632741de` remains documented in the [earlier W200–W249 evidence](../../pr190-localization-2026-11-02/window-200-249/README.md); this packet records a later pass against the catalog state at the pinned head above.

The cross-review covered 600 source-locale cells. It selected 99 exact-hash target changes, retained 489 current targets, and left 12 callerless cells as text-free holds. The held cells contain only identity and current-target hashes in this evidence. All recommendations remain pending native-speaker review.

The application plan contains exact current-target hashes, destination file/blob pins, proposed target hashes, and text-free hold guards. The readback records all 99 changed values; repository evidence confirms 600 cells were read back, exactly 99 translation keys changed across the 12 locale catalogs, and no source, test, workflow, build, or CI changes were made.

At `2026-11-04T16:35:50Z`, PR #190 was open and draft at the exact pinned head. Its API base was `17bde320915af42de73b8646ad56f8ba2ccebf4e`; live `main` was `dbbb46abf8bee2f88e5a8a6ca7d8e141bf4d15a2`. The eight-commit base drift contained only workflows, `AGENTS.md`, retirement documentation, and runner-policy scripts; there were no localization source or catalog changes. See [`cross-review/base-drift-comparison.json`](cross-review/base-drift-comparison.json) and [`pre-apply-live-attestation.json`](pre-apply-live-attestation.json).

## Evidence files

- [`cross-review/`](cross-review/README.md): all 600 cross-review rows, 99 selected changes, rationales, source/context hashes, sealed verifier, live refs, and checksums.
- [`apply-plan.json`](apply-plan.json): exact-hash application plan, including hash-only hold guards.
- [`apply-readback.jsonl`](apply-readback.jsonl): exact readback for the 99 changed targets.
- [`catalog-readback-evidence.json`](catalog-readback-evidence.json): per-file before/after pins, git diff hash, and 600-cell readback result captured before the evidence files were added to the worktree.
- [`apply-result.json`](apply-result.json): readback verification result.
- [`pre-apply-live-attestation.json`](pre-apply-live-attestation.json): PR/branch/pull refs and base drift before application.
- `SHA256SUMS`: checksums for this complete evidence directory, including the nested cross-review packet.

The earlier W200–W249 evidence directory is retained and was not rewritten. No release, tag, merge, test, build, or CI action is part of this follow-up.
