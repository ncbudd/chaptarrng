# ChaptarrNG PR #190 W1200–W1209 exact-head re-review

The original W1200–W1209 tail was already applied at c7e95620c2a89646eb6a37c7e35441804b4911bb. This re-review pins the current exact head c66ef0bccc0635f047cebeda95b9aaa0ae8130a4 after the later dynamic-message clarification. It reattests all 120 source/current/caller cells and applies eight additional corrections/refinements that were still absent at this head.

The original independent review packet is retained unchanged. Its independent-review/summary.json has inconsistent counts; summary-correction.json records the discrepancy. The sealed 120-row cross-review ledger and cross-summary.json agree on 112 accept-current, seven refinements, and one correction (eight changes). Both original checksum manifests are retained.

apply_exact_head.py requires the exact PR head and clean worktree, checks the full target-file and current-value hashes before editing, applies only the eight cross-reviewed values, then reads all 120 final cells back and records their hashes. It does not run tests, builds, scans, CI, or browser work.

## Root reattestation

At input head c66ef0bccc0635f047cebeda95b9aaa0ae8130a4, the separate root verification confirmed exact key-set parity for all 12 direct locale catalogs (4,165 keys each) and preserved each catalog’s original key order, zero placeholder or protected-literal mismatches across 120 cells, and exactly eight changed targets with all non-target locale cells unchanged. git diff --check passed. This was a static catalog review; no tests, builds, scans, or CI were run.
