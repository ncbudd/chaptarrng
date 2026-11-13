# ChaptarrNG PR #190 W1200–W1209 current-head reattestation

Read-only reattestation at exact open/draft PR head `60b5df05d401994955499a837f534974b4276c22` / tree `4c08bd5633244e1d3d07e8b4f1beddab1503a9b3`. It rechecked the prior 120-cell review and cross-reviewed application from `c66ef0bccc0635f047cebeda95b9aaa0ae8130a4` / tree `e2142a119ce8d9d765927bb44a47f71364863995` against the live English source, target catalogs, and every pinned caller-context line.

Result: 120 cells across 10 source IDs and 12 locales; eight target values differ from the old packet input because cross-reviewed values were applied; zero source, target, or caller reattestation failures. All 12 locale catalogs have 4,165 keys and exact key-set parity with English. Live PR metadata and branch/pull refs matched the reviewed head when captured. No source ordinals follow 1209.

`cell-reattestation.jsonl` records cell-level hashes. Run `python3 verify_reattest.py --repo /path/to/chaptarrng` to verify the pinned commit's source, catalog, caller bytes, and artifact checksums. The verifier reads historical Git blobs at the recorded SHA; it does not depend on the PR remaining at that head.

This is static reattestation only. It edits no repository or PR files and runs no tests, builds, scans, or CI. Native-speaker and headed-browser approval were not performed.
