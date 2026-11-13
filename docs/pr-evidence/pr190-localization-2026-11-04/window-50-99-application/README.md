# ChaptarrNG PR #190 W50–W99 application evidence

Applied the sealed independent cross-review at exact base `daa578eaa0d1c252e969d1f5891a364b13d50ec0` / tree `e0b306dc20596ad7004bdfb9ac2cc0a3021726c7`. The PR was OPEN and draft immediately before application.

## Application

- Catalog commit: `ce6460458a31035c7d3361c9e01148a5a4858ca9` (tree `17c3ce829ddd7f4ddfa7778d781daa6dec622169`, direct parent `daa578eaa0d1c252e969d1f5891a364b13d50ec0`).
- Applied exactly 149 selected target values across the 12 direct locale catalogs: 68 corrections and 81 refinements.
- Re-read all 600 cells across 50 source keys and 12 locales: 149 selected values match, 367 accepted-current values remain unchanged, and 84 hash-only holds across seven callerless keys remain unchanged. Held translation/source text is omitted from the hold ledger and application readback.
- Each locale catalog retains 4,165 keys in its original order. Exactly 149 catalog values changed; the catalog commit also adds one unreleased changelog bullet. No workflow path changed.

## Evidence

`cross-audit/` contains the sealed candidate-free, primary, clean-blind, and cross-audit packets with input manifests, complete 600-cell ledger, selected proposals, hash-only holds, and portable verifiers. `source-pin-reattestation.json` records the exact-base source worktree verification. `application-readback.json` records exact pre/post target values for non-held cells and only source/current/final hashes for held cells. `verify_application.py` rechecks all packet checksums, input verifiers, exact commit pins, all 600 target readbacks, the exact 149-cell diff, key order/count, token and protected-literal parity, and hold text-freedom.

## Validation limits

No tests, builds, scans, or CI jobs were dispatched or run for this application. The existing exact-base PR check rollup showed ten `Build ChaptarrNG` jobs as `SKIPPED`; these do not validate this application. No browser review or native-speaker approval is claimed. The PR remains open and draft; no merge, release, or tag was performed.
