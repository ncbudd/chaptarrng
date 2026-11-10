# Manual import regression and release validation (2026-11-10)

## Reproduced defect

The published `v0.9.995` manual-import preview handler calls
`request.finally()`. The AJAX helper returns a jQuery Deferred promise, which
does not implement that method. Executing the published handler through the
real AJAX wrapper and the installed jQuery 4 Deferred reproduces
`TypeError: request.finally is not a function`.

The existing fix in `b4873565af931dd0c0035de7441d99e2f9e254d8` uses
`done`, `fail`, and `always`, ignores superseded responses, and clears only the
active request. It was not included in the latest published stable release
when this validation began. Do not remove the SAB remote-path mapping fix.

Regression commit `b6333252` adds the real-wrapper/real-Deferred case to
`frontend/src/ManualImportAndFileBrowserRecovery.test.cjs`. It covers folder
previews, tracked downloads, preview failure, retry, and cancellation. The
existing test also exercises a late response from a superseded preview.

Confidence is high for this reproduced defect and its regression coverage.
The reporter's exact installation has not been reproduced; no reporter logs
or precise failure stage were supplied.

## Verification

- All 205 discovered frontend tests pass, including the new real-Deferred test.
- Both frontend TypeScript configurations pass.
- The changed test file has no new ESLint findings. Its 25 existing findings
  are unchanged from the parent revision.
- The commit hook's staged Semgrep scan passes with zero findings.
- Exact application source `9b6672c1b869946655bfcdabc419b010d33c5b85`
  passed audit CI run `42871859900`: 5,354 backend tests passed, 48 skipped,
  plus three required direct-download browser tests passed. These browser
  tests do not constitute manual-import UI acceptance.
- PostgreSQL 16 and 17 acceptance passed in run `42871860476`.
- A native Linux x64 candidate from run `42871859992`, at the same application
  source, starts on disposable data. Its authenticated native HTTP manual-import
  endpoint returns the synthetic EPUB fixture as one preview row. This proves
  preview/startup, not successful execution of an import into a populated library.
- Candidate archive SHA-256:
  `687f61db691666874ae3ef8a98971c9cffa699facfc389a970116e7667550e62`.

## Headed browser limitation

The independent Chrome desktop remained on its Kasm background for over three
minutes, so headed manual-import validation was unavailable. No operator
profile or browser session was modified. Failure screenshot artifact
`9594cd77-ff37-4610-9c17-7f983455b253` was persisted through the desktop pool,
and desktop `9295fe3a-b549-42c2-bb4c-e0e2a99a88eb` was released successfully.
Do not count this attempt as visual acceptance.

## Release

Stable `v0.9.998` publication run `42871906657` was already running for the
validated application source. Its native build, installation, migration,
rollback, signing, and publication gates remain authoritative. Publication
has not yet been confirmed in this record; no published assets or tags were
replaced to bypass those gates.
