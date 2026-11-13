# ChaptarrNG PR #190: W350–W399 Core localization

This packet records candidate-free extraction, primary and blind reviews, cross-review, root adjudication, exact-hash application, and full-window readback for the 50-source W350–W399 Core slice.

## Review outcome

All review inputs are pinned to PR head `dbe530c9d1a7fd2c12ce2aef76ec74c5c2188aa0` and tree `be10d71209076f753ef295038a9f3c3646a918a3`. The candidate-free matrix contains 600 cells (50 source IDs × 12 locales).

- Primary: 522 accept-current, 66 proposals, and 12 source-copy holds.
- Blind: 534 accept-current, 22 corrections, 32 refinements, and 12 holds.
- Cross-review: 488 accept-current, 100 recommend-revision, and 12 source-copy holds. The proposal union is 93 cells, with 27 overlaps and 14 identical proposed targets.
- Root adjudication: 99 changes accepted, one recommendation retained as an exact no-op, and 12 source-copy holds maintained.

The 12 held cells are the help text for the `Library` / `All` visibility buttons. The English source describes “Wanted” / “All,” so the existing source does not match the rendered labels. The target cells remain unchanged until that English source copy is corrected and independently reviewed. The separate source-copy review is retained outside this window's application packet.

## Application and readback

The hash-guarded plan applied 99 selected values across the 12 direct locale catalogs. The application record and independent readback verifier both pass. Readback covers all 600 cells, confirms exactly 99 changed cells and 12 changed catalog paths, preserves every non-target catalog value and the English source catalog, and finds no workflow changes. Catalog key counts and ordering remain pinned by the plan and verifier.

Product commit `dcc23d31` consists only of those 12 locale JSON files. This evidence commit adds this review packet separately. The machine review has moderate confidence and does not claim qualified native-speaker approval. No headed-browser review was performed at this head.

## Validation and delivery

The candidate-free, primary, blind, cross-review, root-review, application, and full-window readback manifests and verifiers are included beside their ledgers. `delivery/` records the original PR body, appended suffix, expected body, live API readback, prefix proof, and automatic Actions run. GitHub returned the exact prepared body: 64,252 original bytes remained the exact prefix of the 65,273-byte open, draft PR body. Automatic run `41966481886` completed with all 10 jobs skipped; no build or test ran. `SHA256SUMS.txt` covers every file in this directory except itself.

No tests, builds, scans, CI dispatches, workflow edits, merges, releases, or tags were performed for this window. Git hooks are disabled only as a command-scoped override for the authorized commit and push; no persistent Git configuration was changed.
