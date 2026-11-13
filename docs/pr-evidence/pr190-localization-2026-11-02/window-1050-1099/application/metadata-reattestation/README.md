# Chaptarr W1050–W1099 repaired packet metadata reattestation

This post-review check covers `/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-1050-1099-primary-20261102` against the sealed independent cross-review at `/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-1050-1099-crossreview-20261102` and its exact PR head `c0a098e4e2b23117860c6e6827c1e84485273a7a` / tree `669c5d82ab651dc38abb2db9d35fc2f893a19fef`. The worktree has since advanced to `873405e333415b41feb870c597ef71af9f3dd5b5` / `b979f367a401b54fc35d56c1eac92e5de3b1aa33`; all pin checks below use the earlier commit object directly and the worktree is clean.

## Result

- All 25 primary `SHA256SUMS` entries pass; all 24 manifest artifact sizes and SHA256 values match.
- `README.md` is 3,061 bytes with SHA256 `897127e176748c01d02b61bb77e9faac82a83571ed33c83bf4a31752ab9efbd4`; its manifest entry matches.
- Current `manifest.json` SHA256 is `9b3b0bb0d253d2d5d4cd2513f9777c3dd808f25a976dee72be55c0a78bbe4543`. Current regenerated `SHA256SUMS` SHA256 is `ac1781208ec67b943b7a70aaa0492231f93c7f52beb177cd15c113484d333f9a`.
- All 600 reviewed rows, 50 source records, 12,600 history rows, and 60 caller pins match the sealed cross-review. The 21 pinned source/catalog/caller files still match the pinned Git tree.
- The only primary packet paths with mtimes after the sealed cross-review checksum are `manifest.json` and `SHA256SUMS`; the README and all source/catalog/review data retain their earlier mtimes and match the reviewed content.
- No new semantic dispositions were made. Native-speaker signoff remains outstanding.

Evidence: `manifest-artifact-audit.jsonl`, `checksum-audit.jsonl`, `content-parity.jsonl`, `pin-and-history-audit.json`, and `attestation.json`. `build_attestation.py` reproduces the checks. This attestation packet is confined to task scratch; no repository files, tests, CI, or PR state were changed.
