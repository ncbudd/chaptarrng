# ChaptarrNG PR #190 W250–W299 Core localization follow-up

This evidence folder accompanies product commit `7bf3760ea87879304ec8deb6e4e8cf2f2b62c5b0` (tree `8d821e88af5c3451d608e2bdd87549249d5cf745`), parent `2a9995a2bf63f06814bd8780736305f16bd6b33a`.

The application changed 42 reviewed Core translation cells across 10 locale catalogs and retained the 558 accepted current targets. The apply plan pinned all 12 target catalogs and guarded each changed cell by exact current-target hash before replacement. The readback covers all 600 reviewed cells and verifies the diff contains exactly the 42 planned keys. `verify_application_commit.py` repeats the readback against the committed tree and its exact parent.

The supplemental `root-adjudication.json` corrects `AutomaticUpdatesDisabledDocker::id`: the first cross candidate omitted the source’s first sentence about Docker updates not being directly supported. The corrected target preserves both clauses and `{appName}`. The sealed cross-review packet under `cross-review/` is copied byte-for-byte; the supplemental adjudication does not alter it.

The review and apply are pinned to PR head `2a9995a2bf63f06814bd8780736305f16bd6b33a` and tree `f6ae6530b73bf581c1fbc5a8c13eacd7342e9172`. At pre-apply reattestation, PR #190 was open/draft and branch/pull refs matched that head. Live `main` was 27 commits ahead of the PR API base; the compare had no Core localization catalog/source or frontend caller-file changes. Backend/API files referenced by the broader caller inventory changed, while literal runtime translation callsites did not.

No tests, builds, CI, workflows, merge, release, or tag were run. Git hooks were disabled for the product commit because this checkout’s hooks launch a local security scan, a test script, and a machine-specific package sync.

`SHA256SUMS` covers this folder’s files; `cross-review/SHA256SUMS.txt` seals the copied cross-review packet.
