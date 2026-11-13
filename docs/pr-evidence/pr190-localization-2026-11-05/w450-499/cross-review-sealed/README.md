# ChaptarrNG PR #190 W450–W499 cross-review

This packet combines the independently sealed W450–W474 and W475–W499 cross-review parts. It covers 50 Core source ordinals × 12 locales = 600 cells at PR head `16c809b4787d70616a1a296ab0d90cf17923ba86` / tree `dbd8343a42476f4e830428cc59efb7f4830251d5`, base `025498c1a9deb999a4acd1eafc4c807a252e0c29` / tree `3c27ce1d128d1d74d3b46bf507e2f99f9c02f4d8`, branch `codex/chaptarrng-localization-complete-20261031`.

There are 552 caller-backed decisions and 48 callerless hash-only holds (source ordinals 469, 474, 481, and 482). Held rows in `holds.jsonl` contain no source or current/recommended target text. The combined `ledger.jsonl` includes all caller-backed cross decisions, and `proposals.jsonl` has the 111 exact target changes selected by the cross reviewers.

## Decisions

- 441 caller-backed cells retain current values. 111 receive a reviewed target recommendation.
- The 17 primary/blind disagreements in W450–W474 were adjudicated with explicit wording and rationale.
- Two numeric-token heuristic exceptions are the standard lexicalized octal terms `8進数` (Japanese) and `8진수` (Korean). They do not represent added numeric values; the source word is “Octal.”
- Live main advanced after candidate-free sealing. Global entry/exit PR head, tree, base, branch, pull-ref, and exact worktree pins remained stable; main at each snapshot is recorded separately.
- Confidence is moderate overall; native-speaker signoff was not available.

## Verification

Portable verification checks input and part seals, full 600-cell coverage, primary/blind reconciliation, exact target hashes, hold-text exclusion, and token/number exception records:

```sh
python3 verify_cross_review.py
```

Exact worktree verification also reads the pinned catalogs and Git objects:

```sh
python3 verify_cross_review.py --repo /mnt/disks/scratch/task-worktrees/localization-20261105/chaptarrng-pr190-w400-cross-pinned
```

No repository or PR files were edited. No tests, builds, scans, or CI were run. `SHA256SUMS.txt` seals the combined packet and both review parts.
