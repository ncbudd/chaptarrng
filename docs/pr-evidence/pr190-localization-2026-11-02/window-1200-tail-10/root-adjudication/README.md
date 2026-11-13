# Root adjudication: ChaptarrNG PR #190, positions 1200–1209

This scratch-only package selects one final disposition and target for all 120 current cells across 12 locales. Baseline PR head is `c53c7ac60624926e60ba40f10a88c109cd23a0de`, tree `c2554ab314c96f11ce783faa08896a97e91a4fad`.

## Decision files

- `root-decisions.jsonl`: all 120 decisions, current value and hash, primary and blind targets, caller evidence, resolution basis, and final target/disposition. It resolves all 65 differences.
- `exact-hash-apply-plan.json`: 81 byte-preserving JSON value replacements across 12 locale files. Each operation includes the current value/hash, exact JSON string and line hashes, replacement value/hash, and expected/planned whole-file hashes. This is a plan only; no repository files were changed.
- `reattestation.json`: live PR/ref/tree, source queue, source registry, English catalog, locale target catalogs, source contexts, and all 11 caller pin checks.
- `evidence/`: exact copies of the source queue/attestation, source context, caller pins, p1200 boundary, and PR attestation used for the decisions.
- `adjudication-summary.json`: scope, counts, hashes, and limitations.

## Findings

The pinned queue has 1,210 IDs and ends at position 1209. Positions 1210–1249 are absent; no IDs were invented. The exact PR head/tree, remote branch ref, all 12 target catalog hashes, all 120 current values, and all 11 caller pins were reattested.

The primary recommendation wins positions 1206–1207: all three option labels in position 1206 match exact locale UI keys in all 12 catalogs (36/36), and position 1207 uses the exact localized `Settings` and `Indexers` labels in all 12 catalogs (24/24). Across the 65 differences, 59 final choices use the primary target and 6 use the blind target. Final dispositions are 39 accept-current, 6 refinements, and 75 corrections.

The blind ledger was sealed before primary candidate text was opened. The packet manifest had exposed aggregate disposition counts during verification; no candidate strings were read before the seal. This is machine review only, with no native-speaker approval.

No repository or PR edits, tests, builds, scans, browser work, CI/workflow changes, commits, or releases were performed.
