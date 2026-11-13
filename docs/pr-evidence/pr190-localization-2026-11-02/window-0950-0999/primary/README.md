# ChaptarrNG PR #190 primary localization review — W950–W999

## Scope and pinned state

This primary review covers queue positions 950–999 in the exact currentMissingIds array from docs/localization/source-followup-20261101.json: 50 source IDs × 12 locales = 600 cells. These are zero-based queue positions, not catalog key ordinals.

PR #190 was OPEN/DRAFT at head 961d3102ad3098ee188a6c87a0c88eea5f5ab332, tree c46078c93545042313aa1b35bc3b283b1f3b5406. All seven localization PRs were queried before and after input freeze and after review. Each PR's API head agrees with its API branch ref and HTTPS remote branch ref; no state or head changed during this pass. The final snapshots are in all-seven-pr-heads-*.json.

The worktree at /home/keith/Documents/code/task-worktrees/localization-20261102-chaptarrng was clean at the pinned head. This packet is scratch-only; it did not modify the repository or PR.

## What was reviewed

Every selected source is a native language name in the MyAnonAMouse LanguageFilter enum, shown to users as a provider option. The packet pins the exact English source, provider and server message registries, all 12 complete locale catalogs, the direct enum callsites, and the server-message and provider-option display pipelines. The provider caller rows include the exact source lines and adjacent context. All catalog key sets match.

All 600 current translations were reviewed in their enum and select-option context. The review also checks placeholders, markup, ICU argument signatures, and exact protected literals. Since all selected strings are bare language names, the slice contains no placeholders, markup, ICU syntax, or protected source literals; all structural parity checks pass.

For the 50 Spanish cells, formal/informal address is not applicable: these values are language names without an addressee, instruction, imperative, or second-person form. This judgment is recorded on each Spanish review row.

## Primary decisions

- Accept current: 588
- Correction candidates: 12
- Refinement candidates: 0
- Holds: 0
- Placeholder, markup, ICU, and protected-literal failures in proposed finals: 0

The 12 candidate corrections are:

| Queue position | Locale | Source | Proposed target |
| --- | --- | --- | --- |
| 973 | ar | Icelandic | الأيسلندية |
| 957 | de | Chinese | Chinesisch |
| 980 | de | Korean | Koreanisch |
| 992 | de | Punjabi | Pandschabi |
| 968 | es | Greek, Ancient | Griego antiguo |
| 986 | es | Manx | Manés |
| 992 | es | Punjabi | Punyabí |
| 995 | es | Scottish Gaelic | Gaélico escocés |
| 968 | fr | Greek, Ancient | Grec ancien |
| 992 | fr | Punjabi | Pendjabi |
| 984 | ko | Malay | 말레이어 |
| 999 | vi | Spanish | Tiếng Tây Ban Nha |

Each proposed value and rationale appears in review-cells.jsonl and correction-candidates.jsonl. External dictionary lookups for selected names are listed in external-language-references.json.

## Prior-window continuity

The primary packet reattests all prior queue positions 0–949: 10,800 records for positions 0–899 and 600 applied/cross-reviewed records for W900–949. The W949 boundary matches all 12 applied final targets at this head. Of all 11,400 prior cells, 11,205 live catalog values match their recorded final hashes; 195 differences are confined to positions 0–899 and are retained as prior evidence without being reopened by this window.

The source-884 correction record is included as context only; no W950–999 decision reopens it.

## Limits

This is a machine-assisted static primary review with moderate confidence. It is not an independent cross-review and does not claim native-speaker or browser/runtime approval. Native-speaker approval remains outstanding. No tests, builds, scans, CI, or browser work were performed.

## Packet files

- input-manifest.json, current-missing-ids.json, source-slice.jsonl: exact queue, source slice, and source pins.
- input-cells.jsonl, pinned-files.json: exact current targets, file hashes, Git blobs, and catalog pins.
- caller-context.jsonl, caller-context-summary.json: direct enum callsites and pin audit.
- server-message-pipeline-context.jsonl, provider-option-pipeline-context.jsonl: runtime localization and display paths.
- review-cells.jsonl, language-audit.jsonl: per-cell primary review.
- correction-candidates.jsonl, refinement-candidates.jsonl: exact proposed edits.
- protected-literal-integrity.jsonl, manual-protected-literals.json: structural checks and protected terms.
- prior-disposition-hashes.jsonl, prior-disposition-boundary.json, w949-boundary-reattestation.jsonl: prior decisions and boundary.
- source-884-followup-context.json: out-of-window source correction context.
- all-seven-pr-heads-*.json, final-reattestation.json: live ref checks.
- manifest.json, SHA256SUMS: packet inventory and integrity hashes.
