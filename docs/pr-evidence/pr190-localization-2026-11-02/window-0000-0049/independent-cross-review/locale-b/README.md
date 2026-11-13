# ChaptarrNG PR #190 W0–49 locale B cross-review

- Exact review head: `7bb2b2f977e81d214318b3f873afe8ab17f03ed5`
- Exact tree: `5fdb46e8b55083b44f6ca109b1e46fd5b375b7cb`
- Primary packet: `/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0000-0049-primary-semantic-20261102/primary-decisions.jsonl`
- Assigned locales: ja, ko, pt-BR, vi, zh-Hans, zh-Hant
- Reviewed cells: 300 (50 per locale)
- Cross-review dispositions: accepted 283; refined 0; missed 17; held 0; noop 0
- Native-speaker approval: false
- Blockers: none

## Review and validation

Each JSONL row retains the primary identifying, source, current-target, caller, and head/tree fields. `primaryReason` and `primaryConfidence` preserve the primary review fields. The cross-review uses `disposition`, `reason`, and `confidence`; a proposed replacement appears as `target` with its UTF-8 SHA-256 in `targetSha256`. Accepted unchanged rows omit both target fields.

The review verified that all 300 rows point to the pinned head/tree; all source strings match `src/NzbDrone.Core/Localization/Core/en.json` and the first 50 `currentMissingIds`; all current catalog strings and hashes match; and all 804 caller references match the pinned trimmed source line, current line coordinate, and full-line hash. Proposed replacements were checked for bracketed placeholder parity and protected product/file/API terms. The Aria2 `XML-RPC` protocol spelling was normalized in four labels.

No repository files were changed. No tests, builds, scans, CI, releases, or other execution workflows were run. This is a language-model cross-review and does not qualify as native-speaker approval.
