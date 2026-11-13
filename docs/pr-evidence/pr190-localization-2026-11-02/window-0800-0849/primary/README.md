# ChaptarrNG PR #190 primary semantic review — W800–W849

## Exact input and source window

PR #190 is OPEN/DRAFT at `f0eb9d38b1989bd6e3addeb698ec8c5f9c29d9e9` / tree `7f0f9a9d71d672bb47c08e1abe4125be03d815d6` on `codex/chaptarrng-localization-complete-20261031`. The GitHub PR, GitHub branch ref, official GitHub remote, and clean worktree were reattested before and after review. The worktree remains clean.

The source queue is `currentMissingIds` from `docs/localization/source-followup-20261101.json` at the exact head, pinned by the complete ordered-list SHA-256 `a16dd0001c0a36f053bf0207060c338c428dc9beb2e3d929f7d73f19ad004e8c`. The queue has 1,210 unique IDs. This packet covers positions 800–849, IDs `server.message.mbdf9bc8e9c84` through `server.message.mdca0d476f941`, 50 source IDs × 12 direct locales = 600 cells. The selected ID list SHA-256 is `6328f7e2287bbecfb477f4571547f93ae136f251bb5808a6fbbe2804d1076b01`. It is disjoint from all positions 0–799.

All 12 direct locale catalogs, the English source catalog, the source registry, 63 production callsite references, and 76 generic frontend server-message display pipeline references were pinned by blob and SHA-256. There are no source caller or generic pipeline gaps. W799's source, caller context, and 12 live locale values match the previous independent cross-review final at this head.

Prior exact-hash evidence covers all positions 0–799: 9,600 per-cell disposition records across 16 windows / 19 packet files. Packet checksums passed; the record SHA-256 values, current/final target hashes, and dispositions are in `prior-disposition-hashes.jsonl`. No prior cell overlaps W800–W849.

## Decisions

- `accept-current`: 364
- `propose-correction`: 234
- `propose-refinement`: 2
- `hold`: 0
- Candidate targets: 236

Every cell has the exact English source, current target, final primary target, hashes, caller context and rationale. All proposed targets preserve the verified placeholders, markup, and protected literals. Current placeholder and markup mismatches are 0; final mismatches are 0. One current protected-literal mismatch is corrected: the Brazilian Portuguese MonitorExistingMode value currently translates the JSON sentinel `null` as `nulo`; the proposal preserves exact `null`.

Key context reviewed includes BookshelfNG edition selection, RanobeDB release-vs-work IDs, opaque exception interpolation, enum values, indexer category warnings, Calibre library paths, Goodreads shelves and list imports, and provider IDs. The `{value0}` from the import-list feed and Apprise API response remains opaque.

Confidence is moderate and machine-assisted. Native-speaker review remains outstanding. No repository or PR files were changed; no tests, builds, scans, CI, browser, workflow, release, tag, or merge activity was performed.
