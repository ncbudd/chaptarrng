# ChaptarrNG PR #190 exact-head localization re-review input, positions 50–99

This input packet freezes 50 provider-field source IDs and 600 direct-locale cells at PR head `22e3dc28193113e29d256307b4c75b856d7cd84f` / tree `605a751ae9c3b454f4189dd89d021a5976e95237`. The slice uses positions 50–99 of the pinned `currentMissingIds` list and is disjoint from the first window, positions 0–49. Each row includes exact source and target value hashes, catalog blob pins, and current production-caller line hashes.

The repository reports an aggregate historical review covering 14,520 cells, but the per-cell ledger is absent. Consequently this packet is a fresh re-review of exact current values; overlap with that aggregate is unknown and is not claimed to be new coverage. Known row-level evidence for these provider-field IDs was checked separately.

This packet is preparation only. Semantic dispositions, independent cross-review, qualified native-speaker signoff, and headed browser review are not yet complete. No repository edits, tests, builds, scans, CI, workflow changes, releases, tags, or merges were made.
