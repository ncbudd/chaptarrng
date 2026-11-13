# ChaptarrNG PR #190 W475–W499 cross-review part

This part covers source positions 475–499 (25 IDs × 12 locales = 300 cells) from the fresh W450–W499 candidate-free packet. It contains 276 caller-bound semantic decisions and 24 hash-only callerless holds. The held source keys and source/current target text are intentionally absent from the part output.

Pinned PR head/tree: `16c809b4787d70616a1a296ab0d90cf17923ba86` / `dbd8343a42476f4e830428cc59efb7f4830251d5`; base `025498c1a9deb999a4acd1eafc4c807a252e0c29`; branch `codex/chaptarrng-localization-complete-20261031`. Live `main` had advanced after candidate-free sealing; entry and exit snapshots record current `main` while the reviewed PR head/base and exact worktree remained stable.

All 61 primary/blind proposal cells in this half are adjudicated. Wording corrects Chown group semantics, technical `gid`, indexer flags, action labels, calendar grouping, colon replacement, completed-download settings, component terminology, and Hindi condition spelling. The octal help recommendations use written-language words instead of adding a numeric `8`. Token checks pass. Confidence is moderate; no native-speaker signoff was available.

Callerless rows remain in `holds.jsonl` with hashes and position/locale metadata only.

Portable verification:

```sh
python3 verify_part.py
```

Exact pinned worktree verification:

```sh
python3 verify_part.py --repo /mnt/disks/scratch/task-worktrees/localization-20261105/chaptarrng-pr190-w400-cross-pinned
```

Candidate-free, primary input-bound, and blind exact worktree verifiers passed before adjudication. No repository or PR files were edited.
