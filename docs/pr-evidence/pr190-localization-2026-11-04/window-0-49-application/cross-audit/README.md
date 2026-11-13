# ChaptarrNG PR #190 W0–W49 independent cross-audit

This bundle reconciles all 600 localization cells from the primary review and an independent blind review against the candidate-free source packet. It is pinned to commit `7f5d99e24b054cf1437d135328c3dee565e6b318`, tree `d39f2fe8cf91a39653679980c0832c5ca400a114`.

## Results

- 514 cells: keep the current translation.
- 38 cells: select an evidence-backed proposed revision.
- 48 cells: hold without proposed wording because four author-monitor keys have no exact frontend caller context.
- No repository or PR files were modified. This review is not native-speaker approval.

The primary and blind input packets are included under `input/` with their original manifests. `work/reviewer-a.jsonl` records a separate candidate-free-only review of ordinals 0–24; it accepted those 300 current values. The cross-audit independently adjudicates disagreements, including 14 supported changes within that range.

## Files

- `cross-ledger.jsonl`: one row per cell, source/current hashes, both review dispositions, evidence links, and cross-audit outcome. Held rows omit source and translation text.
- `selected-proposals.jsonl`: 38 selected targets, hashes, placeholder/protected-literal checks, caller evidence, and rationale.
- `cross-audit-holds.jsonl`: 48 hash-linked holds with no source, current, or proposed wording.
- `summary.json` and `summary.md`: counts, scope, and limitations.
- `verify_cross_audit.py`: integrity and consistency verifier. Optionally pass `--source-worktree PATH` to verify the exact Git checkout, catalog values, and caller lines.
- `create_cross_audit.py`: rebuilds the ledger, selected proposal file, holds, and summary from the included packets and reviewer workpaper.
- `SHA256SUMS.txt`: checksums for every bundle file except this checksum list itself.

## Verify

```sh
python3 verify_cross_audit.py
python3 verify_cross_audit.py --source-worktree /mnt/disks/scratch/task-worktrees/localization-20261104/chaptarrng-pr190-w0-49-apply
```

The second command additionally requires the pinned checkout path. The source checkout was clean at the time of review.
