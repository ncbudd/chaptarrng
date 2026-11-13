# ChaptarrNG PR #190 primary semantic review: currentMissingIds 0–49

This primary review covers 50 source IDs and all 600 direct-locale target cells at PR head `7bb2b2f977e81d214318b3f873afe8ab17f03ed5` / tree `5fdb46e8b55083b44f6ca109b1e46fd5b375b7cb`. The input packet was built from the first 50 `currentMissingIds` in `docs/localization/source-followup-20261101.json`; all source and current target hashes were re-attested at this head, and all 134 source-to-caller references were rechecked. Each caller line string occurs exactly once at its current location.

The caller registry’s stored line numbers shifted for 86 references. They were not trusted as current coordinates; exact source lines and hashes were located at the updated lines in 19 files. The 50 source IDs have no overlap with the 101-cell exact-head reconciliation or other row-level dispositions found in the repository’s `docs/localization` evidence.

## Primary decisions

- Accepted unchanged: 535
- Correction candidates: 65
- Uncertain: 0
- Held: 0

Correction candidates are exact current-value replacements with UTF-8 target hashes, rationale, confidence, source pins, caller references, and protected placeholder checks in `primary-decisions.jsonl`. Every proposed correction preserves the source’s bracketed placeholders, file extensions, and named application/provider values. This is a primary review; it has not been independently cross-reviewed and no catalog or PR was changed.

This is not qualified native-speaker approval. Headed browser review is not part of this primary packet. No tests, builds, scans, CI, workflow changes, releases, tags, or merges were run.
