# ChaptarrNG PR #190 primary semantic review - W900-W949

This scratch-only review covers queue positions 900-949: 50 source IDs x 12 direct locales = 600 cells. These are zero-based positions in the exact currentMissingIds list from docs/localization/source-followup-20261101.json; they are not catalog-key ordinals. PR #190 was OPEN/DRAFT at a9a74f6ba733e8c1f06a2d260bd802d4fde2da0e / tree d9d25f309f3a7256056b4ed8deb1dabee58b64fe at input freeze and final reattestation. All seven localization PR refs were queried before and after the review; each PR API head, branch API ref, and HTTPS remote branch agreed in the recorded snapshots.

## Decisions

- Accept current: 478
- Correction candidates: 71
- Refinement candidates: 51
- Holds: 0
- Placeholder and markup mismatches in final proposals: 0
- Protected-literal failures in proposals: 0
- Current values missing an explicit protected term: 7; all are resolved in proposed corrections.

review-cells.jsonl is the per-cell decision ledger. correction-candidates.jsonl and refinement-candidates.jsonl contain exact proposed targets and hashes. language-audit.jsonl is the full 600-cell language-review export of this same primary pass; it is not an independent second review. protected-literal-integrity.jsonl records current, proposed, and final placeholder, markup, and literal checks.

## Source and caller evidence

All 50 exact English sources and 12 complete locale catalogs were reattested. Direct caller context covers 50 source rows and 86 exact caller references, with zero gaps or stale caller pins. Server-message display evidence covers 76 pinned references. Provider-option rendering/localization evidence covers 20 pinned code references, including enum FieldOption, server-side SchemaBuilder/ILocalizationService localization, and the frontend select display path.

The W899 boundary matches all 12 prior cross-review final targets at the frozen head. Prior review packets cover positions 0-899 with 10,800 exact cell records and no queue-position overlap. At this head, 10605 current prior-window values match their recorded prior final hashes and 195 do not; every comparison is retained in prior-disposition-hashes.jsonl. Those older differences are recorded, not reopened by this window.

The source-884 backslash/source correction and its specific language follow-up remain separate and outside W900-W949. This packet does not reopen any source-884 locale decision.

## Scope and limits

This is a machine-assisted static primary review with moderate confidence. Native-speaker review remains outstanding. No repository or PR files were edited, and no tests, builds, scans, CI, or browser work were run.

## Evidence files

- input-manifest.json, current-missing-ids.json, source-slice.jsonl: exact queue and source slice.
- input-cells.jsonl and pinned-files.json: exact current targets, hashes, catalog blobs, and file pins.
- caller-context.jsonl, server-message-pipeline-context.jsonl, provider-option-pipeline-context.jsonl: caller and runtime display context.
- prior-disposition-hashes.jsonl, prior-disposition-boundary.json, w899-boundary-reattestation.jsonl: prior decisions and boundary.
- source-884-followup-context.json: context-only out-of-window source correction record.
- all-seven-pr-heads-*.json and final-reattestation.json: live ref checks.
- manifest.json and SHA256SUMS: file integrity.
