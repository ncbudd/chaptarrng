# ChaptarrNG PR #190 W600–649 independent cross-review

Pinned to live PR #190 at `f405a6256c2661e48e412ac4471ce70411baf98c` / tree `fe3272572b68460f1d8c8083a5dcc44cd3307b74`; PR state remains open/draft. The primary packet’s supplied `SHA256SUMS` digest is `953d11509d8fbec61b361b3306f0a4f2cf1b3f51af3559bd823b3d6d2351e42f` and all listed files verify. Its exact-head source/catalog input hashes also verify.

## Findings

- Reattested all 600 current source/target cells, 64 caller references across 42 exact C# files, and each of the 201 candidate recommendation hashes.
- Rebuilt and checked the 1,210-ID ordered source list; positions 600–649 match the primary slice.
- Rechecked the W599 previous-window edge: the source/callers match; 6 current targets still match the older primary values and 6 match that packet’s recommendations after application. Reattested the next source W650 across 12 locales.
- Candidate outcomes: 198 primary proposals accepted; 3 rejected and replaced; no holds.
- The three W621 primary targets for “Category is recommended” instead ask which books to monitor when adding discovered authors. The pinned caller is a qBittorrent warning for an absent audiobook category. Replacements are recorded in `missed-issues.jsonl`.
- Rechecked placeholders, markup, protected literals, and hashes. The primary has 15 current protected-literal misses; all proposed and cross-review final targets preserve them.
- The repository and PR were not modified. No tests, builds, scans, CI, browser actions, workflow edits, releases, or tags were run. Native-speaker approval remains outstanding.

## Packet files

- `live-cell-reattestation.jsonl` — 600 exact-head source/current catalog rows and hashes.
- `caller-ref-reattestation.jsonl` — 64 line, context, blob, and file hash checks.
- `boundary-reattestation.jsonl` and `boundary-next-source-650.jsonl` — W599 and W650 edges.
- `candidate-cross-review.jsonl` — independent disposition of all 201 proposals.
- `missed-issues.jsonl` — three rejected W621 targets and replacements.
- `final-dispositions.jsonl` — one final decision for each of 600 cells.

All packet files are checksummed in `SHA256SUMS`.
