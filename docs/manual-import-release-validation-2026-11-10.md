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
- The newer full native audit `42873840212` passed all eight installed recovery
  targets on `b6333252`, including Windows x64/x86, macOS x64/ARM64, Linux
  x64/ARM64, and Linux musl x64/ARM64. Only regression tests differ from the
  earlier application source; no application or build inputs changed.
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

Stable `v0.9.998` publication run `42871906657` did not publish. Besides its
macOS runner problem, its Linux x86 installed handoff failed while restarting
the unchanged BookshelfNG `.76` predecessor after declining conversion.
The predecessor logged `DryIoc.ContainerException`, unable to resolve
`NzbDrone.Core.Messaging.Events.IEventAggregator`. The harness had already
verified that declining conversion left the source snapshot unchanged.
This is not evidence of a ChaptarrNG startup failure, nor a passing Linux x86
handoff. Preserve the original failed source logs and database evidence.

The signed Windows x64 candidate from that unpublished run is 174,118,389 bytes
(166.05 MiB), below the 190,000,000-byte budget. SHA-256 is
`2d1512980b5660d642dfb6d40006499e506c4f186d8bc952974c9d23e486cf32`.
Its checksum and ZIP CRC checks pass. SkiaSharp's runtime DLL, Playwright, and
the updater remain; SkiaSharp's PDB and the unused Db2 driver are absent.
These figures describe the unpublished `.998` candidate, not a later release.

A concurrent release session committed `5c5159f2`, selecting `macos-26` for
native ARM64 installed validation and advancing the version to `0.9.999`.
It started publication run `42887913617`. That run completed successfully.
No published assets or tags were replaced to bypass its gates.

## Published result

- `v0.9.999` became the latest stable GitHub release on November 10, 2026,
  at `21:06:47 UTC`, from `5c5159f21a313521c21ec3b5506e54c21a02f6e1`.
- All ten standalone archives built and passed their updater signature policy.
  All nine installed migration/forced-rollback gates passed, including Linux
  x86 and macOS ARM64 on `macos-26`. The earlier predecessor failure remains
  recorded above; no source-health assertion was weakened to obtain a pass.
- The public `ChaptarrNG-0.9.999-win-x64.zip` is 174,118,279 bytes (166.05 MiB).
  Its public release digest matches the independently downloaded artifact:
  `a881e703cef9a5dacb5ee82c637df6ec95e1d2dce99d10f55aa110a846df92d6`.
  ZIP CRC, checksum, and updater trust-policy verification pass. Playwright,
  the updater, and the SkiaSharp runtime remain; the unused Db2 driver and
  SkiaSharp PDB are absent. The 190,000,000-byte budget is satisfied.
- `chaptarrng.0.9.999.nupkg` was pushed successfully to Chocolatey at
  `21:12:03 UTC`. Submission does not establish moderator approval. The legacy
  BookshelfNG Chocolatey identity was not pushed: its migration-bridge
  publication gate remains disabled, unchanged by this task.
- Discord destination verification and posting passed. Retained receipts:
  [changelog](https://discord.com/channels/1447333772419928256/1569406962800656495/1569820718764396606)
  and [ChaptarrNG project channel](https://discord.com/channels/1447333772419928256/1552357772975280199/1569820720605958287).
- The verified Windows archive, checksum, signature bundle, and verification
  manifest are retained on `kspld0` under
  `~/code/task-deliverables/chaptarrng-manual-import-20261110/`.
