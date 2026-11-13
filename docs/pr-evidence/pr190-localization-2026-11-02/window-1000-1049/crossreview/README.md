# ChaptarrNG PR #190 W1000–W1049 cross-review

## Scope and snapshot

This packet independently reviews all 600 locale cells for source positions W1000–W1049 across ar, de, es, fr, hi, id, ja, ko, pt-BR, vi, zh-Hans, and zh-Hant. The repository was pinned at `c28d0ab23b2c5454a10237496e642b2ad059d8ce`, tree `bd7a8a32a8bffc2a3168b648ff6e22d368064e5b`.

The primary packet at `/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-1000-1049-primary-20261102` passed its `SHA256SUMS` verification. `input-attestation.json` records the primary packet hashes. `live-pr-snapshots-start.json` and `live-pr-snapshots-end.json` record all seven live localization PR heads and Git trees at the start and end of review.

## Cross-review decisions

| Decision | Cells |
| --- | ---: |
| Accept current | 503 |
| Accept current with German style note | 1 |
| Accept primary proposal | 83 (50 corrections, 33 refinements) |
| Additional W1047 ellipsis refinements | 2 |
| Retain primary hold for native review | 11 |

All 83 primary proposed values were independently accepted. None was rejected or rewritten. Two additional refinements restore the ellipsis in the Spanish and Brazilian Portuguese eBook-smell lines, because the source pause sets up the punchline. The German W1048 line remains accepted; a note asks a native reviewer to check formal `Sie` against the nearby informal loading-copy voice.

All 11 holds remain holds: W1000 Vietnamese Castilian Spanish; W1047 Arabic, Hindi, Indonesian, Japanese, Korean, Vietnamese, Simplified Chinese, and Traditional Chinese; W1049 Arabic and Indonesian. No speculative replacement was supplied for those cells.

## Exact-value and context checks

`cross-review-ledger.jsonl` has 600 unique rows and carries the exact current values/hashes, primary value/hash/disposition, independent disposition and target/hash, source text/hash, caller context hash, caller refs, registry context, protected literals, and structural check results.

Independent rechecks confirmed all 600 current values and hashes against their exact locale catalog files. The 53 distinct pinned caller lines and registry lines match the exact worktree after trimming source indentation; the primary records 58 direct references across the 50 source IDs. All 75 pinned source/caller files match their exact byte, SHA-256, and Git blob pins. Current and reviewed targets preserve source placeholders, markup, ICU signatures, and protected literals. `independent-structural-audit.json`, `source-caller-context-reattestation.json`, `caller-pin-reattestation.json`, and `pinned-file-reattestation.json` contain the checks. All 50 source/caller records and queue IDs match the sealed source slice.

## Limits

This is static machine-assisted cross-review, not native-speaker approval. Confidence is high for exact hashes, caller pins, and structural checks; semantic confidence is moderate overall. The 11 holds and all-locale native review remain outstanding. No browser, external dictionary, app edit, PR edit, test, build, scan, CI run, commit, push, or release action was performed.

## Files

- `cross-review-ledger.jsonl`: all 600 decisions.
- `findings.json`: the two additional refinements, German style note, and retained holds.
- `summary.json`: scope, counts, confidence, and validation status.
- `independent-structural-audit.json`: source/current/final hash and structural verification.
- `caller-pin-reattestation.json`: live caller and registry line verification.
- `pinned-file-reattestation.json`: all 75 pinned file checks.
- `input-attestation.json`: primary packet and initial live snapshot hashes.
- `live-pr-snapshots-start.json`, `live-pr-snapshots-end.json`: all-seven PR head/tree snapshots.
- `manifest.json`, `SHA256SUMS`: cross-review packet checksums.
