# ChaptarrNG PR #190 W400–449 exact-hash review and application

Primary and independent cross-review covered 50 source IDs × 12 locales (600 cells) at input head 2eb0ae6eb15ebc366eea44dd969265c0f6366445 / tree 1340ba7d0642217aa81e3789e908931bd6fa74f1. The cross-review reattested 90 caller references across 27 files with zero mismatches.

Final dispositions were 488 accept-current, 53 correction proposals, 47 refinement proposals, and 12 holds. Applied 100 exact-hash target changes across all 12 locale catalogs; each catalog retains 4,165 keys. Placeholder, markup, and protected-literal mismatch counts are zero.

The 12 held cells are ordinal 447, “Failed to import author: {value0}”. The nearby API validation path interpolates arbitrary exception text and does not use the localized key, so the source remains held. W399 boundary targets and caller references were reattested.

Primary and cross-review packets, exact apply plan, readback, and checksums are retained here. Qualified native-speaker and current-head browser review remain outstanding. No tests, builds, or CI were run. The commit-time Semgrep Community Edition hook scanned three staged evidence-builder Python files with p/default (290 rules; zero findings); it did not scan product source. No workflow changes, releases, tags, or merges were made.
