# W350–W399 Core primary review

This review covers all 600 cells (50 English Core source keys × 12 locales) from the candidate-free packet pinned to PR head `dbe530c9d1a7fd2c12ce2aef76ec74c5c2188aa0` / tree `be10d71209076f753ef295038a9f3c3646a918a3`, with latest main `0d711ce1a9828675e879b2ba97f36fc3b9544188`.

The primary review records **522 accept-current**, **66 proposed revisions**, and **12 text-free holds**. The holds are the `BookVisibilityToggleHelpText` cells: source says “Wanted” while the pinned UI button is “Library”, so no translation target was selected pending source/context reconciliation. The manual-shelf placeholder proposals preserve the exact Goodreads shelf names `read` and `currently-reading`.

All proposals are exact-hash and caller-context bound in `primary-review-cells.jsonl`; `primary-review-proposals.jsonl` contains only proposed text. The 16 protected-literal heuristic flags for `ID`/`LAN` were manually reviewed and are not automatic holds.

This is machine-assisted primary review, not native-speaker approval. The current-window blind and cross-review outputs were not accessed. Exposure and scope are recorded in `review-process-exposure.json`; see `primary-review-summary.json` for per-locale and per-key proposal counts.
