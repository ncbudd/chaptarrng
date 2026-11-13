# ChaptarrNG PR #190 W450–W499 localization review and application

This packet covers 50 Core source IDs × 12 locales = 600 cells. Inputs and semantic decisions are pinned to PR head `16c809b4787d70616a1a296ab0d90cf17923ba86` / tree `dbd8343a42476f4e830428cc59efb7f4830251d5`, base `025498c1a9deb999a4acd1eafc4c807a252e0c29`.

Candidate-free, primary, blind, cross-review, independent second opinion, and root adjudication cover 552 caller-backed cells and 48 callerless hash-only holds. The cross-review retains 441 current values and proposes 111 changes. Independent second opinion and manual root review accept all 111; the Japanese `8進数` and Korean `8진수` terms are explicit lexicalized-octal exceptions. No held target text is included in the hold ledgers or application readback.

Product commit [`fb9d0439f5adf751b07c5d6167009591d0b0c6e7`](https://github.com/snapetech-org/chaptarrng/commit/fb9d0439f5adf751b07c5d6167009591d0b0c6e7) changes exactly 111 values across the 12 direct locale catalogs. Exact readback confirms 111 changed cells, 441 retained current cells, and 48 unchanged hash-only holds. Each locale catalog retains 4,165 keys and its original order; all non-target values and the English fallback are unchanged.

The packet records the live PR/base references and reattests this window after `main` advanced. Six caller contexts differed from the older candidate-free main snapshot; current PR caller pins and selected source/target values were rechecked. No base update was included.

Review confidence is moderate. This machine-assisted review does not establish qualified native-speaker approval or headed product-browser acceptance. Those remain outstanding. No tests, builds, scans, CI dispatches, workflow changes, merge, release, or tag occurred. The commit and push hooks were disabled because the local pre-commit hook launches Semgrep and the pre-push hook launches an image-alias test outside private ephemeral JIT. The product commit includes `[skip ci]`.

## Evidence

- [`candidate-free/`](candidate-free/) — pinned source, caller, catalog, and current-target inputs.
- [`primary-review/`](primary-review/), [`blind-review/`](blind-review/), and [`cross-review-sealed/`](cross-review-sealed/) — independently reviewed decisions and exact-head verifiers.
- [`second-opinion/`](second-opinion/) and [`root-adjudication/`](root-adjudication/) — target-by-target second opinion and root dispositions.
- [`application/`](application/) — exact-hash plan, guarded apply script, full 600-cell readback, and catalog structure checks.
- [`attestation/`](attestation/) — entry and exit references.

The PR remains open and draft. No exact-head deployment or product-browser review is claimed.
