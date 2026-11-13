# Cross-audit report

## Result

- Cross-audited all 31 selected cells across 7 source IDs and 12 locales.
- Primary and blind dispositions agree for **31/31**: accept-current. Recommended target strings and SHA-256 hashes agree for **31/31**; no correction, refinement, or hold recommendation differs.
- All 31 cell/selection, source text, current target, catalog, caller, placeholder, protected-literal, and exact head/tree checks pass against the candidate-free packet. Both output `SHA256SUMS` files and the packet `SHA256SUMS` verified.
- Source corrections at ranks 654 and 695 are confirmed for all 24 affected locale rows: corrected source hashes match the packet’s current source hashes, and caller snapshots pin the SABnzbd instruction and Mailgun test-send failure.
- All 7 changed existing catalog cells have current target hashes matching the selected-cell manifest and locale snapshots; blind catalog path/blob/SHA pins match the manifest.

## Confidence variance

There is no disposition or recommended-text disagreement. Confidence differs for one cell: `notification.heading.renamed` / `zh-Hant` is `high` in the primary ledger and `moderate` in the blind ledger. The target (`已重新命名`) and its hash are identical. This is a confidence-rating variance only.

The primary ledger does not serialize per-cell catalog pins or caller line hashes. Its cell keys and target hashes were checked against the packet manifest, and its caller path/line references were checked against packet snapshots. The blind ledger contains exact catalog pins and caller line hashes; these match the packet. The blind correction-evidence object omits the correction git blob field, which was checked independently against the packet manifest and full source-correction evidence.

## Integrity

- Packet head/tree: `580538d38f92e0ec005366ff6bea3f2634400c2e` / `b61f7ca1f5b496c01a32ba7b8f3520076ec5cfc1`.
- Packet attestation reports a clean worktree. No repository or PR was queried or changed during this audit; no tests/builds/CI were run.
- See `cross-audit-ledger.jsonl` for per-cell comparisons and checks.
