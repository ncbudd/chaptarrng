# ChaptarrNG PR #190 primary semantic review: W700–749

This packet reviews 50 source IDs across 12 locales (600 current locale cells).

## Exact input pin

PR #190 remains OPEN/DRAFT at `02f0d841b54c7806005fc67973973799c6960bcf` / tree `eab2516e48adf4586f14cb131dc1ca6876f87e5f` on `codex/chaptarrng-localization-complete-20261031`. The API, remote branch, and detached worktree were rechecked before input capture and after review generation; the worktree is clean. Ordinals use `currentMissingIds` from `docs/localization/source-followup-20261101.json`.

W650 primary and independent cross-review packets verify. All 600 W650 live locale targets match the independent final targets at this head. Its two source follow-ups are now present: ordinal 654 names `SABnzbd` correctly, and ordinal 695 says `through Mailgun`. W699's source, callers, and 12 current locale targets match the prior cross-review boundary. W700–749 source IDs have no overlap with prior windows.

## Review results

- Decisions: {'accept-current': 403, 'propose-correction': 197, 'propose-refinement': 0, 'hold': 0}; 197 candidate corrections and 0 holds.
- Source callers: 77 exact references across 50 files, with 50 source rows and no gaps. Two source-registry line pins were refreshed against current production lines (711 and 746).
- Generic frontend server-message display path: 76 line references across 35 files; no gaps.
- Placeholder mismatches current/final: 0/0. Markup mismatches current/final: 0/0.
- Protected-literal mismatch cells current/final: 0/0.

`review-cells.jsonl` and `primary-review-ledger.jsonl` contain one decision per locale cell with exact source/current/final values and hashes, caller context, rationale, confidence, and token checks. `correction-candidates.jsonl` lists each proposed target. `prior-w650-reconciliation.json` and `w699-boundary-reattestation.jsonl` preserve the previous applied window and boundary evidence.

Native-speaker approval remains outstanding. No repository/PR files or workflows were changed; no tests, builds, CI jobs, browser actions, releases, tags, or merges were run.
