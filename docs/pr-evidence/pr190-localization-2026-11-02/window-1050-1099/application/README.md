# ChaptarrNG PR #190 W1050–W1099 application

Application input was PR head `c0a098e4e2b23117860c6e6827c1e84485273a7a` / tree `669c5d82ab651dc38abb2db9d35fc2f893a19fef`. The exact-hash applier verifies both sealed review packets, the corrected primary manifest, all 600 source/current/final hashes, protected `Dodge` literals, and placeholder/ICU/markup parity before writing the 42 independently confirmed corrections and refinements.

`exact-hash-apply-plan.jsonl` contains the 42 changed cells; `full-window-apply-plan.jsonl` records all 600 review decisions. `catalog-preapply-pins.jsonl`, `full-window-readback.jsonl`, and `catalog-postapply-attestation.json` record exact before/after values and key order. `apply-summary.json` records the resulting counts. The live all-seven PR snapshot and primary-packet metadata reconciliation are included.

Run `python3 apply-reviewed-window.py` from the repository at the pinned pre-apply head to reproduce the application. The script rejects any head, tree, packet, catalog, source, or target hash drift.

An independent post-review metadata reattestation is preserved under `metadata-reattestation/`. It verified all 25 primary packet checksum entries and all 24 manifest artifacts, then compared 600 reviewed rows, 12,600 historical rows, and 60 caller pins against the sealed cross-review with zero mismatches. It used the pinned input commit directly after the PR branch advanced; it made no new semantic decisions. The attestation packet has its own manifest and checksums.
