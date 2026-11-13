# ChaptarrNG PR #190 push-hook disclosure

On 2026-11-02, documentation commit `841f0a514d38f28476179d0c3f91774f5c10063c` (`docs(i18n): refresh Chaptarr review status`) was pushed to `codex/chaptarrng-localization-complete-20261031`. Its parent was `45e8e228433da1ed107ff7825652d6d1d903e5ea`; it changed only `docs/localization/server-copy-review.md`.

The exact push command was:

```sh
git push origin HEAD:refs/heads/codex/chaptarrng-localization-complete-20261031
```

The commit used `git -c core.hooksPath=/dev/null commit`, but the push command did not disable hooks. The repository's local pre-push hooks therefore ran on `kspld0` and printed:

> ChaptarrNG and BookshelfNG retirement release-readiness gates passed.
> Single standard image alias contract tests passed.

This hook output was unexpected and occurred outside the required private ephemeral JIT environment. It is recorded for transparency and does not satisfy or replace private-JIT validation. No tests, builds, scans, or CI were intentionally invoked for the documentation commit, and none were repeated after this hook ran.
