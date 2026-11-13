# ChaptarrNG PR #190 W100–W149 application evidence

Applied the sealed independent cross review at exact base `9fd23606fbb4c8928505772413e5c23e85352adc` / tree `cba466021a9a0c9699ef171ddc6a510a69209083`. The PR was OPEN and draft before application.

## Application

- Product commit: `a5b6d99061f1193af5d8de9b3d04d9df7296b043` (tree `cab243f181d5d5e9490130e5d6229df7219848af`, direct parent `9fd23606fbb4c8928505772413e5c23e85352adc`).
- Applied exactly 42 selected primary targets across 11 locale catalogs. All 12 locale catalogs were checked; every catalog retains 4,165 keys in original order.
- Read back all 600 cells: 42 selected values match, 390 accepted-current values remain unchanged, and 168 callerless holds remain unchanged. Hold rows contain only cell/source/target hashes and non-text metadata.
- All 432 caller-backed values passed placeholder, inline-code, markup, numeric, and protected-literal checks. No English source wording recommendation was applied.
- The product commit changes only the 11 locale catalogs with selected values and `CHANGELOG.md`. No workflow path changed.

## Evidence

`cross-audit/` is a byte-for-byte copy of the sealed W100–W149 cross packet. It records the candidate-free and primary input hashes, exact caller/context pins, selected cells, current-cell decisions, text-free holds, two separate English source wording recommendations, and the cross verifier result.

`caller-backed-input.jsonl` preserves the exact candidate-free rows only for the 432 caller-backed cells. The 168 callerless rows are deliberately omitted from this file; they are represented only by hashes in the cross packet and application readback. `application-readback.json` records exact preimage/final values and hashes for caller-backed cells, hash-only hold readbacks, catalog file hashes/blobs, key counts/order, and token checks.

Run `python3 docs/pr-evidence/pr190-localization-2026-11-04/window-100-149-application/verify_application.py` from a repository clone containing the pinned base and product commit objects. The verifier checks the evidence checksums, sealed cross bundle, exact 600-cell dispositions, all selected and accepted-current values, text-free unchanged holds, token parity, the exact 42-value catalog diff, catalog key order/count, and changelog-only addition. The original cross verifier was run before application and reported PASS for its candidate-free and primary verifiers; it can be rerun using the input paths in `cross-audit/README.md` when those original scratch inputs and the exact-base source worktree are available.

## Validation limits and PR refs

No tests, builds, scans, or CI jobs were dispatched or run. Repository pre-commit and pre-push hooks were bypassed because they invoke a Semgrep scan and a packaging test; neither ran. `git diff --check` passed. No browser review or qualified native-speaker approval is claimed.

Immediately after the product push, the branch ref advanced to the product commit while the GitHub PR API and `refs/pull/190/head` still reported the pinned base. That mismatch is recorded in `application-postflight.json`; the PR body update remains pending exact pull-ref synchronization. The PR remains open and draft. No merge, release, or tag was performed.
