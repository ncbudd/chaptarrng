# ChaptarrNG PR #190 push-hook disclosure — 2026-11-03

Commit 0f8012dc431d4f0aac439d1122eaa5f3c8080132 (fix(i18n): review Chaptarr localization window 1150-1199) was pushed to codex/chaptarrng-localization-complete-20261031. Its parent was 6e7a5341b7ccac31d950c73db68277f9a1f18f8e. It changed the twelve locale catalogs and added the W1150-W1199 review evidence.

The push used the normal repository pre-push hook. The hook at .githooks/pre-push ran packaging/scripts/test-publish-image-aliases.sh on kspld0 and printed:

> ChaptarrNG and BookshelfNG retirement release-readiness gates passed.
> Single standard image alias contract tests passed.

This hook ran locally, outside the required private ephemeral JIT environment. The output does not satisfy or replace private-JIT validation. No CI was dispatched. The checks were an automatic side effect of pushing; they were not separately requested, and they will not be repeated for this task.
