# Local deepmerge security patch

This package starts from upstream `deepmerge` 4.3.1 (MIT). The GitHub advisory
`GHSA-gcqx-w48m-w2h4` reports prototype poisoning with no upstream patched
version. The patch filters `__proto__`, `constructor`, and `prototype` keys
before copying either source or target properties into a merged result.

Both the CommonJS and UMD distributions carry the same change. The local
resolution applies to the two build-time transitive dependents, and the Docker
build contexts copy this package before `yarn install --frozen-lockfile`.

Run `node scripts/test-patched-deepmerge.mjs` for the poisoning and ordinary
merge cases. Remove this patch when a reviewed upstream fixed release exists.
