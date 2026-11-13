# ChaptarrNG PR #190 W550–599 independent cross-review

- Exact PR state reattested as open/draft at `015ff68d96340292b5e6a45d34496a5936ebf09c` / tree `bbb59a14a50a4b63bc209663c1e4b873ead4fc10`.
- Scope: 50 source strings × 12 locales = 600 exact source/current/candidate cells. The primary packet manifest and all its listed source/catalog inputs were independently checksum-verified.
- Primary disposition counts reattested: 329 accept-current, 240 corrections, and 31 refinements.
- Exact source and current catalog values were re-read from the pinned commit. All 600 source/current hashes, candidate hashes, caller-context hashes, placeholders (including multiplicity), markup, and protected literals were checked.
- Caller review: 50/50 source rows, 69 references across 42 files, reattested against exact line text, adjacent context, blob IDs, and file SHA-256.
- Primary candidate outcomes: 256 retained, 3 revised, 12 held. There are 7 new findings on cells the primary marked accept-current.
- Final cell dispositions: {'accept-current': 322, 'propose-correction': 233, 'propose-refinement': 33, 'hold': 12}.
- Revised candidates: `555|id`, `583|ar`, `583|ko`. New current-target findings: `574|ar`, `580|de`, `580|ja`, `580|fr`, `580|pt-BR`, `580|ar`, `597|vi`.
- Hold: all 12 W561 cells. The English source says KeepHistory “should be less than 25000,” while the pinned caller rejects only values above 25000 and accepts exactly 25000. Locale options that say “must not exceed 25000” are recorded separately in `revisions-and-holds.json`; they are not accepted targets until the English source wording is decided.
- W549 boundary: 12 source/locale rows and caller context reattested; 8 older current targets still match, and 4 prior recommendations now match the live catalog.
- This is a model cross-review, not native-speaker approval. No catalog edits, PR writes, tests/builds/scans/CI, browser actions, workflow edits, or releases were performed.

Detailed records are in `candidate-cross-review.jsonl`, `full-cell-final-dispositions.jsonl`, `live-cell-hash-reattestation.jsonl`, `caller-reattestation.jsonl`, `caller-reference-reattestation.jsonl`, and `W549-boundary-reattestation.jsonl`. `SHA256SUMS` checksums every packet file except itself.
