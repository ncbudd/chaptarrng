# ChaptarrNG PR #190 W1150-W1199 root adjudication

This packet records independent recommendations for the 138 cells where the primary and independent cross-review packets differed. It compares the exact English source, caller context, current target, both review candidates, and the blind third-review proposal. Decisions were made from source and caller semantics plus target wording; candidate vote counts were not used as a rule.

## Exact revision and checks

- PR head: 6e7a5341b7ccac31d950c73db68277f9a1f18f8e
- Tree: d073e1373021bf715db37461a12654f7e993cdbf
- Clean PR worktree: /mnt/disks/scratch/task-worktrees/localization-20261030/chaptarrng-main-699b0a
- Exact-head readback checked all 138 source values, current locale values, source/target file hashes, caller file hashes, and caller line hashes. See exact-head-reattestation.json.
- Placeholder counts and protected technical/API literals were checked for every selected recommendation. ICU patterns and markup are absent in these rows.
- Upstream primary, cross-review, third-review, and root-input SHA-256 values are recorded in manifest.json.

## Results

- Rows: 138
- Dispositions: {"refinement": 53, "correction": 64, "accept-current": 21}
- By locale: {"ar": 6, "es": 6, "fr": 9, "pt-BR": 11, "vi": 19, "zh-Hans": 15, "zh-Hant": 15, "hi": 10, "ja": 15, "ko": 18, "de": 11, "id": 3}
- No semantic holds remain in this adjudication.
- Every row remains pending qualified native-speaker review. This machine adjudication does not establish native-speaker approval.

## Editorial points adjudicated

- The ReleaseController error occurs when book extraction from parsed release metadata yields no matching books; “identify/find books” wording was retained where it better fits that user-facing caller than a syntax-parsing claim.
- Live conversion/progress/finalization messages use ongoing status wording; ready-to-import targets say the artifact is ready, not already imported.
- Technical identifiers, API fields, tool names, protocol labels, paths, counts, percentages, duration values, and M4B remain literal/dynamic as pinned.
- French enabled-client counts use count-neutral wording to avoid artificial client(s) inflection. French protocol-availability errors now say no client is available, avoiding a scope-ambiguous double negative.
- Locale-specific grammar fixes were applied where the blind third-review accept-current result still had an evident grammar or meaning problem; the row retains all three alternative review results for root audit.

## Delivery boundary

This packet is scratch-only. No repository or PR was changed. No tests, builds, scans, CI, browser sessions, workflow edits, release, tag, or merge were performed.

Confidence is moderate for the machine language adjudication. All 138 cells require qualified native-speaker review before localization signoff.
