# ChaptarrNG PR #190 — W1150–W1199 independent cross-review

## Exact-head attestation

- Repository: `snapetech-org/chaptarrng`, PR #190 (open, draft)
- Branch: `codex/chaptarrng-localization-complete-20261031`
- Head: `6e7a5341b7ccac31d950c73db68277f9a1f18f8e`
- Tree: `d073e1373021bf715db37461a12654f7e993cdbf`
- Local worktree, official remote branch, and PR head/tree matched at final re-attestation (`final-reattestation.json`). The local worktree was clean.

## Review coverage and result

- 50 English source IDs × 12 locales = **600 independently reviewed cells**.
- Dispositions: **455 accept-current**, **82 correction**, **51 refinement**, **12 hold**.
- The 12 holds are all locale cells for W1187 (`server.message.md764ed5e74b4`). Both pinned callers supply `TargetQualityName ?? "M4B"`; configured names can vary while the source registry protects `M4B`. No fixed runtime meaning was inferred.
- W1170's nested alternate-client sentence is handled by the existing frontend localization path. Exact caller, formatter, matcher, and template pins are recorded in `caller-context-findings.jsonl`; no additional source/caller gap is reported.
- Caller audit: 59 direct caller references in 7 files, zero caller gaps, and zero caller pin mismatches against the primary packet.
- Structural checks over reviewed proposals: zero placeholder, markup, or ICU mismatches. The current catalog has 11 protected-literal mismatches at W1187; all 12 W1187 cells remain held because the dynamic value may differ even where the current target includes `M4B`.

## Comparison with primary packet

The primary packet was consulted only after the independent ledger was sealed. Across 600 cells there are 462 exact disposition/target agreements, 48 differing candidate targets, 12 same-target/different-disposition-kind cases, 62 primary candidates not independently confirmed, and 16 independent candidates omitted by primary. Per-cell differences are preserved in `primary-comparison-differences.jsonl` for coordinator adjudication; the independent dispositions remain unchanged.

## Method and limits

The review used the exact-head English sources, all 12 target catalogs, source registry, and pinned production caller contexts. It is a static, machine-assisted semantic review with overall **moderate confidence**. It does not claim native-speaker approval, browser acceptance, runtime validation, tests, builds, scans, or CI. No repository files or PR metadata were changed.

## Key artifacts

- `independent-review-cells.jsonl`: complete 600-cell independent ledger.
- `independent-correction-candidates.jsonl`, `independent-refinement-candidates.jsonl`, `independent-holds.jsonl`: filtered dispositions.
- `caller-context-findings.jsonl`: W1170 handled route and W1187 dynamic-literal hold evidence.
- `primary-comparison-summary.json`, `primary-comparison-differences.jsonl`: post-seal comparison.
- `inputs/`: exact-head source/catalog/caller evidence and input checksums.
- `final-reattestation.json`: final PR, remote, and worktree pin check.
- `SHA256SUMS`: checksums for every packet file except this checksum file. `manifest.json` lists file sizes and hashes.
