# ChaptarrNG PR #190 W1187 cross-audit

This packet cross-audits source ordinal 1187 (`server.message.md764ed5e74b4`) at exact live PR head `00d37b25ce5534135c2dacaf6a84d9d15fe0bb0b` / tree `13e57e7826db4db86556f244fb066e4915022511`. The source registry and both exact `ConversionJobService.cs` callers were re-read and hash-checked. They establish that `M4B` is the null fallback passed as dynamic `{value0}`, not protected source text; the current registry has an empty protected-literal list.

The earlier W1150–W1199 primary and independent cross packets held all 12 cells with `M4B` recorded as protected. The current blind packet accepts all 12. At the requested head, 9 current hashes are unchanged from those old held cells; German, French, and Vietnamese now match the later exact-hash correction/refinement plan already read back into the catalogs. All 12 current targets retain `{value0}` once and do not hardcode `M4B`. The cross-audit clears all 12 prior holds and selects 12 no-op actions: 0 updates, 12 no-ops, 0 holds.

The verifier rechecks the candidate-free and blind packets, prior W1150–W1199 evidence checksums, current source registry/callers/catalogs, source and target hashes, prior-hold lineage, later exact-hash readback, local/remote refs, and live PR metadata. One generated `__pycache__/compare-primary-after-independent.cpython-314.pyc` entry is absent from the old top-level and cross-review checksum lists; all other listed entries passed, including the primary and independent-review subpacket lists. No repository/PR files were edited; no tests, builds, CI, or browser review were run. Native-speaker approval was not obtained.

Run `python3 verify_cross_audit.py` and `sha256sum -c SHA256SUMS.txt` in this directory.
