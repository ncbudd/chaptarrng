# ChaptarrNG PR #190 W400–449 independent cross-review

- Exact PR pin: OPEN/DRAFT at `2eb0ae6eb15ebc366eea44dd969265c0f6366445` / tree `1340ba7d0642217aa81e3789e908931bd6fa74f1`, reattested before and after review.
- Scope: 50 source IDs × 12 direct locales = 600 independently judged cells.
- The complete primary packet was copied to `primary-packet/`; its input and output checksum manifests pass. All live source/catalog values and caller lines were reattested at the pinned tree.
- Reviewed all 88 primary correction/refinement candidates, retained the 12-cell hold at W447, and found 12 additional current-target issues. Full final strings, hashes, caller references, and structural checks are in `cross-review-cells.jsonl`.

## Results

- 488 cells: accept current.
- 85 primary candidate targets: accept.
- 3 primary candidates: revise (W407 pt-BR, W414 pt-BR, W449 zh-Hant).
- 12 additional corrections/refinements: W413 es/vi; W414 hi; W421 hi; W434 es; W436 ko; W445 es, zh-Hans, ja, ko, zh-Hant, id.
- W447 remains held in all 12 locales. No source-ID or approved literal-source caller is pinned for this key. `AuthorController.cs:945` interpolates raw `ex.Message` into a different ValidationFailure and is not evidence that this catalog ID renders. Keep the translations unresolved until the actual caller and `value0` meaning are mapped.
- W399 boundary: all 12 prior primary and cross-review dispositions remain `accept-current`; current values, final targets, and three caller references match live data.
- Final independent disposition: 53 correction candidates, 47 refinement candidates, 12 holds, and 488 accepted current values.
- Placeholder, markup, and protected-literal mismatches in all final targets: zero.

Confidence is moderate. Semantic review is model-based; native-speaker approval remains outstanding. No repository/PR edits, tests, builds, scans, CI, browser actions, or workflow edits were performed. The repository worktree is clean.
