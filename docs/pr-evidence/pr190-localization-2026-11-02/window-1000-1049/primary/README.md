# ChaptarrNG PR #190 primary localization review — W1000–W1049

## Exact scope and snapshot

This packet reviews queue positions 1000–1049 from `docs/localization/source-followup-20261101.json`. Positions are zero-based queue offsets, not English catalog key order. The selection contains 50 provider/source labels and 600 locale cells across ar, de, es, fr, hi, id, ja, ko, pt-BR, vi, zh-Hans, and zh-Hant.

ChaptarrNG PR #190 was OPEN and DRAFT on branch `codex/chaptarrng-localization-complete-20261031` at head `c28d0ab23b2c5454a10237496e642b2ad059d8ce`, tree `bd7a8a32a8bffc2a3168b648ff6e22d368064e5b` when this packet was sealed. Seven localization PR heads and trees were queried before the source slice was frozen (2026-11-02T21:57:31.973724+00:00–2026-11-02T21:57:33.373897+00:00 UTC) and immediately after source selection (2026-11-02T21:57:52.816200+00:00–2026-11-02T21:57:55.053864+00:00 UTC). A final seven-PR reattestation (2026-11-02T22:04:44.596526+00:00–2026-11-02T22:04:45.862238+00:00 UTC) found no head/tree movement. Full GraphQL responses are under `snapshots/`.

The worktree at `/home/keith/Documents/code/task-worktrees/localization-20261102-chaptarrng` was clean at the exact head. All review artifacts are in task scratch; no repository, PR, workflow, release, or remote state was changed.

## Review result

All 600 current values were reviewed against the English source, pinned enum/validator/loading caller, and the current locale catalog. The packet records 506 accept-current decisions, 50 correction candidates, 33 refinements, and 11 holds.

| Disposition | Count |
| --- | ---: |
| Accept current | 506 |
| Correction candidate | 50 |
| Refinement candidate | 33 |
| Hold for native-language review | 11 |

Candidate detail is in `correction-candidates.jsonl`, `refinement-candidates.jsonl`, and `holds.jsonl`; `review-cells.jsonl` contains all 600 decisions and exact UTF-8 hashes. Candidate text is a review proposal, not an applied repository change.

Structural checks cover placeholder multiplicity/order-insensitive parity, markup, ICU signatures, and exact registered protected literals. Final reviewed values have 0 placeholder, 0 markup, 0 ICU, and 0 protected-literal failures. Registered literals include `POST`, `PUT`, `Freeleech`, `VIP`, `Chaptarr`, and `chaptarr`; every proposed final preserves its exact source-registered literal. For the eBook joke, the internal terminology record calls for preserving `eBook` casing where the language permits, but it is a soft terminology instruction rather than a protected literal.

## Caller, terminology, and formality evidence

`source-slice.jsonl`, `caller-context.jsonl`, `pinned-files.json`, and the three pipeline context files pin all 50 selected sources to their exact caller lines and the provider-option, server-message, and loading-message presentation paths. All direct caller pins resolved; no registry line was stale.

`internal-terminology-references.json` records the exact repository terminology guidance for eBook and audiobook, plus source-registered protected literals. No external dictionary/CLDR browsing was performed because this task prohibited browser work; candidate language-name spellings that would benefit from an external authority remain subject to native-language review.

`locale-formality-review.json` summarizes all 12 locale registers. Spanish is mixed across the existing catalog: general UI often uses informal tú, while corresponding unsuffixed folder-permission errors use usted. The W1039/W1040 refinements align with the paired error messages. German uses formal Sie for error guidance and may use informal du in playful loading copy; French uses polite vous in user-directed guidance; pt-BR uses polite você/third-person imperatives. Other locales use their normal polite/neutral user-instruction forms where direct address appears. Bare enum labels have no addressee.

## Boundary and prior-decision continuity

`prior-dispositions-through-W999.jsonl` preserves all 12,000 prior cell dispositions and final hashes from positions 0–999. For W950–W999 it carries the full primary review, applied target hashes, cross-review dispositions for the 182 rows recorded in the prior cross-review ledger, and adjudication dispositions for the 182 recorded rows; other rows are explicitly marked as not present in those partial ledgers. `prior-review-evidence-pins.json` pins those earlier ledgers and readback. It also records current-head live-value hash comparisons. W999's 12 final targets all match the current catalogs (`w999-boundary-reattestation.json`). W1050 is pinned with its exact English source and all 12 current targets as boundary context only; no W1050 disposition is assigned (`w1050-forward-boundary.json`). No prior positions were reopened.

## Independent focus review

A separate agent reviewed W1021–W1049 (348 cells) at the same pinned head. Its independent findings were adjudicated into the primary ledger: priority agreement, book-condition grammar, Indonesian/Spanish/French/Vietnamese filesystem terms, placeholder placement, and Hindi loading-state wording are represented as candidates. The eBook smell joke is held for native-language review in Arabic, Hindi, Indonesian, Japanese, Korean, Vietnamese, Simplified Chinese, and Traditional Chinese. The exact adoptions and retained findings are recorded in `independent-focus-review.json`. This is another machine-assisted pass, not native-speaker approval.

## Native-speaker status and limitations

Native-speaker approval is **not present** and remains outstanding for all 12 locales. This is a static, machine-assisted primary review with overall moderate confidence; several candidates and all holds are explicitly marked moderate/low. There was no browser, runtime, or native-speaker review. The packet does not claim final linguistic certification.

## Packet contents

- `input-manifest.json`, `selected-queue-window.json`, `source-slice.jsonl`: exact queue selection and source pins.
- `input-cells.jsonl`, `pinned-files.json`: exact current translation values, hashes, Git blobs, and catalogs.
- `caller-context.jsonl`, `caller-context-summary.json`, `*-pipeline-context.jsonl`: direct caller and display-path evidence.
- `review-cells.jsonl`, `language-audit.jsonl`: full per-cell primary decisions.
- `correction-candidates.jsonl`, `refinement-candidates.jsonl`, `holds.jsonl`: proposed changes and held cells.
- `protected-literal-integrity.jsonl`, `internal-terminology-references.json`, `locale-formality-review.json`: structural, terminology, and register review.
- `prior-dispositions-through-W999.jsonl`, `w999-boundary-reattestation.json`, `w1050-forward-boundary.json`: continuity and boundaries.
- `snapshots/`, `final-reattestation.json`: exact live PR-head snapshots.
- `manifest.json`, `SHA256SUMS`: sealed inventory and integrity hashes.
