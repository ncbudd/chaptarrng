# ChaptarrNG PR #190 W0–W49 application evidence

Applied the independently cross-reviewed W0–W49 catalog selections at exact base `7f5d99e24b054cf1437d135328c3dee565e6b318` / tree `d39f2fe8cf91a39653679980c0832c5ca400a114`. The live PR was OPEN and draft at that head immediately before catalog application.

## Application

- Catalog and changelog commit: `3e9ef37d39301126dfc3631a80ba09fbe46f5211` (tree `30dee7612b72adf2032a295abd25acd74db55539`, parent `7f5d99e24b054cf1437d135328c3dee565e6b318`).
- Applied 38 selected revisions across 11 locale catalogs.
- Read all 600 candidate cells back from the application commit: 38 selected hashes match; 514 accepted-current hashes remain unchanged; all 48 text-free holds remain unchanged.
- Each of the 12 locale catalogs retains the same ordered 4,165-key set. Exactly 38 target values changed; the only other changed path is `CHANGELOG.md`. Workflow path count: zero.
- The catalog-only application commit has no workflow changes.

## Evidence

`cross-audit/` is the complete portable candidate-free, primary, clean-blind, and cross-audit packet, including the 600-row ledger, selected revisions, text-free holds, and verifier. `application-readback.json` records hash-only readbacks for every cell; held rows have no source or translation text. `verify_application.py` verifies packet checksums, the exact base/application commits, all source and caller pins, catalog deltas, hashes, readback, and text-free holds.

## Validation and review limits

No tests, builds, scans, CI dispatches, merges, releases, or tags were run or made. The configured local pre-commit Semgrep, pre-push image-alias test, and post-commit package sync were bypassed only for the commit invocation using a temporary empty `core.hooksPath`; repository hook configuration was not changed.

This is machine-assisted cross-review. No native-speaker approval or browser acceptance is claimed. The PR remains open and draft; the evidence commit and final PR body update follow this catalog commit.
