# ChaptarrNG PR #190 primary semantic localization review

This directory contains the independent primary semantic review requested for the candidate-free packet at `/mnt/disks/scratch/task-scratch/chaptarrng-pr190-review-gap-packet-20261103/`.

## Pin and scope

- Repository: `snapetech-org/ChaptarrNG`
- PR: #190
- Head: `580538d38f92e0ec005366ff6bea3f2634400c2e`
- Tree: `b61f7ca1f5b496c01a32ba7b8f3520076ec5cfc1`
- Selected decisions: 31 cells across 7 exact source IDs and 12 locales
- Consistency context: 53 additional locale snapshots, not separately adjudicated

## Files

- `per-cell-ledger.jsonl`: one decision per selected cell, including source/current/recommended text and hashes, caller references, source-correction pins where relevant, rationale, confidence, and literal/placeholder checks.
- `summary.md`: scope, decision counts, and review basis.
- `SHA256SUMS`: hashes for the two report files and this README.

## Method and result

The review used only files in the candidate-free input packet. It did not consult PR body or earlier review output, query or mutate a PR, edit repositories, or run tests/builds/CI. The corrected English strings at source ranks 654 and 695 were checked against the packet's correction evidence and current production callers. All 31 current targets are accepted as semantically adequate. No changes are proposed, so each `recommendedTarget` equals `currentTarget` and the hashes match.

Confidence is `moderate` on the Hindi transliteration of the Home Assistant discovery label and the Japanese “Missing Books” sensor label; the packet's context supports their current meanings but does not establish a more specific local product term.
