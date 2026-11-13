# ChaptarrNG PR #190 primary semantic review — W850–W899

This scratch-only packet reviews 50 source IDs at queue positions 850–899 across all 12 direct locales (600 cells). PR #190 was OPEN/DRAFT at `175cff3a50569b67def345bb82332b30e9bb378c` / tree `e682581e3c577b62215658c374b15a9d3f8f8bd0` when the exact source and catalogs were frozen and again at finalization. All seven live localization PR refs were queried; the matching API, branch-ref, and HTTPS remote heads are recorded in `all-seven-pr-heads.json`.

## Review results

- Accept current: 509
- Correction candidates: 69
- Refinement candidates: 10
- Holds: 12
- Candidate target hashes, source/caller pins, protected-literal checks, placeholders, and markup are in `review-cells.jsonl` and `protected-literal-integrity.jsonl`.
- Re-attested caller context: 74 references across 50 source rows; gaps: 0. Generic server-message display pipeline refs: 76; gaps: 0.
- Placeholder mismatches: 0; markup mismatches: 0; protected-literal failures in proposed targets: 0.
- The W849 boundary matches all 12 previously cross-reviewed final targets at the current head. All 600 W800–W849 applied targets were re-attested against the live catalogs. Prior review coverage through W849 is recorded as 10,200 exact cell dispositions, with zero overlap against this window.

## Hold and limits

All 12 W884 cells are held. The English source catalog says `Can not contain '', '//', or start/end with '/'`, but the exact qBittorrent caller also forbids `\`. The translation source omits this instruction. Align the source and caller first, then review all 12 translations again. The exact caller text and hashes are included in the cell rows and `primary-findings.json`.

This is machine-assisted static semantic review with moderate confidence. Native-speaker review remains outstanding. No repository or PR files were changed; no tests, builds, CI, or browser work were run.

## Build and limits

`prepare_input.py` freezes the source/catalog/caller rows. `reconcile_prior.py` verifies the checksummed W800 evidence and replaces the temporary compatibility scan with the complete 10,200-cell predecessor ledger through W849. Then `make_primary_review.py` records all 600 decisions and `finalize_packet.py` reattests the head and checksums the packet.

## Exact evidence

- Source queue: `current-missing-ids.json` contains the pinned 1,210-ID list; its canonical ordered-list SHA-256 is `a16dd0001c0a36f053bf0207060c338c428dc9beb2e3d929f7d73f19ad004e8c`.
- Source slice and current values: `source-slice.jsonl`, `input-cells.jsonl`.
- Caller and display-pipeline context: `caller-context.jsonl`, `pipeline-caller-context.jsonl`.
- Prior dispositions and boundary readback: `prior-disposition-hashes.jsonl`, `prior-disposition-boundary.json`, `w849-boundary-reattestation.jsonl`, and `w800-w849-applied-reattestation.jsonl`.
- Final live state: `final-reattestation.json`; checksums: `SHA256SUMS`.

## Independent language audit addendum

A separate static language audit now covers all 79 correction/refinement candidates and all 12 W884 holds. It accepts 69 correction candidates and 10 refinements; it found no candidate revisions or added proposals. The 509 accept-current cells remain in the primary ledger and are outside the independent addendum scope. See `language-audit-addendum/README.md` and its per-cell ledger/checksums. Native-speaker review remains outstanding.
