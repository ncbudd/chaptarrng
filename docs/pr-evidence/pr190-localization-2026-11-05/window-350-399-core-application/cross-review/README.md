# W350–W399 cross-review artifacts

The independent ledger was produced from `candidate-free/input` only and sealed before either proposal ledger was opened. It covers all 600 cells for source ordinals 350–399 and binds each row to the exact source text, current target, caller-context fingerprint, token summary, file hashes, and PR head/tree.

The pinned review target is PR #190 head `dbe530c9d1a7fd2c12ce2aef76ec74c5c2188aa0`, tree `be10d71209076f753ef295038a9f3c3646a918a3`. No repository checkout, PR body, browser, or external source was used for the independent pass.

`independent-review.jsonl` contains one pre-proposal decision per cell. The independent seal records 542 accept-current, 46 replacements, and 12 text-free holds. Its SHA-256 is recorded in `independent-review-manifest.json` and `SHA256SUMS.txt`.

After sealing, the primary and blind proposal packets were verified and compared row by row. `final-cross-review.jsonl` binds all three reviews to the candidate-free source/current/caller/token hashes and records every proposal with its exact target hash. `cross-recommendations.jsonl` is the 100-row target extract; `cross-holds.jsonl` lists the 12 cells with no target text. The final cross decision count is 488 accept-current, 100 recommend-revision, and 12 hold-source-copy.

The visibility-help rows remain on hold. Cross-only supplemental evidence supplied after the independent seal shows that the control renders localized `Library` / `All` labels while the English help source says `Wanted` / `All`. The recommended follow-up is to align the English source copy to “Library shows monitored books and books with files. All shows every book for this author,” then conduct a separate focused review of the corrected source and its 12 targets. `visibility-label-context.json` records the exact localized labels supplied for all 12 locales. The independent ledger remains unchanged.

Run the portable standard-library verifier from any directory:

```sh
python3 verify_cross_review.py
```

Or pass the task scratch root explicitly. The verifier checks the candidate-free, primary, blind, and cross-review checksums; the exact head/tree pin; all 600 source/current/caller/context/token bindings; proposal target hashes; recommendation hashes; placeholder, markup, inline-code, and numeric-token preservation; and the text-free visibility holds.
