# ChaptarrNG PR #190 W50–W99 primary review bundle

Created on kspld0 for the next 50 uncovered English Core keys in snapetech-org/chaptarrng.

## Exact source pin

- PR: https://github.com/snapetech-org/chaptarrng/pull/190
- Live state after review: OPEN/DRAFT
- Head: daa578eaa0d1c252e969d1f5891a364b13d50ec0
- Tree: e0b306dc20596ad7004bdfb9ac2cc0a3021726c7
- Remote branch and local source worktree match that head/tree.
- The source worktree is clean.

## Selection and candidate-free input

The sealed candidate-free packet contains 600 cells: 50 ordered English Core keys × 12 target locales. It pins all 13 catalogs, caller contexts from 1,634 frontend files (100 direct translation references), and the 392 historical window JSONL files used to choose the batch. The scan found no direct historical identifier overlap with this block. Placeholder and protected-literal signatures are recorded.

The prior manifest reports 1,160 Core keys in semantic disposition rows; the broader direct identifier scan over all 392 historical JSONL files intersects 1,212 Core keys. These counts describe different scopes and are preserved separately. The W0–W49 source-selection list reattests as the first 50 uncovered keys under the broad scan; this packet is the next 50.

## Primary review

- 401 cells accept current wording.
- 139 cells recommend focused revisions.
- 60 cells are text-free holds across five keys where direct caller context or dynamic placeholder composition is insufficient.
- Placeholder parity and protected literals pass.
- Native-speaker approval: 0; native-speaker review remains outstanding for all 600 cells.

The primary ledger is a recommendation packet. No catalog or repository file was modified. Blind review and cross-adjudication are still required before application.

## Verification

Run these commands from this directory:

    sha256sum -c SHA256SUMS.txt
    sha256sum -c candidate-free-SHA256SUMS.txt
    sha256sum -c primary-review-SHA256SUMS.txt
    python verify_candidate_free.py --source-worktree /mnt/disks/scratch/task-worktrees/localization-20261104/chaptarrng-pr190-w0-49-apply
    python primary-review/verify_primary_review.py --source-worktree /mnt/disks/scratch/task-worktrees/localization-20261104/chaptarrng-pr190-w0-49-apply
