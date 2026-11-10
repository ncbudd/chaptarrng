# Package acceptance handoff — 2026-11-10

This is the execution checklist for a local agent with disposable platform VMs.
It distinguishes the **published ChaptarrNG v0.9.995 release** from the
**unpublished BookshelfNG identity-bridge candidates**. Do not publish or
enable a legacy feed as part of this acceptance exercise.

## Pin inputs and preserve evidence

- Release tag: `v0.9.995`; release source commit:
  `c570d7524a07eacaee0920a6cb01ac2e63c6f80a`.
- Use a clean checkout at that commit for an exact-release test; record any
  separate fixes made on `main` and repeat the affected test at the new SHA.
- Download candidates from the [published release](https://github.com/snapetech-org/chaptarrng/releases/tag/v0.9.995).
  Verify every archive against its own `.sha256` sidecar before unpacking.
  Keep the `.sigstore.json` bundle and use
  `packaging/scripts/verify-release-update-bundles.py` for the repository's
  signed-update/attestation gate; SHA-256 alone establishes integrity against
  the downloaded sidecar, not publisher identity. Pin the predecessor archive
  and its SHA-256 from `.github/workflows/published-installed-handoff.yml`.
  For packages, verify package identity, version and source checksum as well.
- Use a new task-scoped directory and fresh disposable VM or container for
  each installed test. Never point a harness at an operator's live data.
  Record OS image and kernel, CPU architecture, package-manager and platform
  versions, both artifact hashes, source revision, mode (No/Manual/Yes),
  service health, source and backup fingerprints, rollback result, test log,
  and disposition (`pass`, `fail`, `blocked`, `not run`). Redact credentials and
  personal book metadata before retaining logs. A blocked test is not a pass.

## What is already validated

The v0.9.995 release workflow [42715733054](https://github.com/snapetech-org/chaptarrng/actions/runs/42715733054)
built the ten standalone archives and their SHA-256 and Sigstore sidecars,
verified updater signatures and published the release. It passed installed
migration/forced rollback for Linux x64, arm64, musl x64, musl arm64, x86,
macOS x64, macOS arm64, Windows x64 and Windows x86. The standard multiarch
container image built and pushed. These checks use synthetic predecessor
fixtures; they do not prove every operator database or platform catalog.
The [security audit record](../security/audit-remediation-2026-11-09.md)
contains the corresponding regression and scan evidence.

In this restricted workspace, the following **source/package contracts**
passed: 34 legacy-channel Node cases; desktop and container candidate
builders with synthetic fixtures; Debian and PPA publish gates; image alias
contract; six release-bundle parser tests; and 24 runner-policy tests.
Those builder tests do not install a real v0.9.995 package. The publisher
configuration test could not start because this host's `gpg-agent` cannot
create a Unix socket (`Operation not permitted`). Repeat it on a host with
working GPG IPC. Docker, Podman, VM, Windows, RPM and Flatpak tooling are not
available here; no installed-channel claim is made from this workspace.

## Install matrix for the local agent

| Channel/artifact | Environment and executable check | Current acceptance |
| --- | --- | --- |
| Nine standard release archives: Linux x64/arm64/musl x64/musl arm64/x86, macOS x64/arm64, Windows x64/x86 | Published assets and pinned `.76` predecessors; rerun `.github/workflows/published-installed-handoff.yml` with `release_tag=v0.9.995` or reproduce the workflow's architecture-specific harness and retain evidence. Use native OS and matching architecture; Linux musl and x86 run in their pinned Docker images, not a glibc host process. | Passed on hosted runners for v0.9.995; repeat only for an independent OS/device or operator fixture. |
| `freebsd-x64` release archive | Fresh FreeBSD 15.1 x64 VM with `sqlite3`, compatible OpenSSL and `libiconv`; verify `.76` predecessor and v0.9.995 archive/sidecars, then exercise `scripts/bookshelfng-standalone-launch.sh` No, headless Manual, Yes/health, source backup, injected failure and recovery. Follow the FreeBSD VM procedure in the [historical channel record](BOOKSHELFNG_CHANNEL_ACCEPTANCE_2026-10-26.md#freebsd-standalone-installed-acceptance), but substitute the exact v0.9.995 archive and record new hashes. | Archive built and signed; **current release installed migration/rollback outstanding**. |
| ChaptarrNG Docker image, Compose, Unraid template | Docker host, then actual Unraid host/Community Applications for its template. Pin the published OCI index digest. Check old `/config`, `/books`, `/downloads` mounts, No/Manual/Yes where supported, health, update and forced rollback. `packaging/scripts/test-docker-installed-compatibility.sh` and `packaging/unraid/README.md` provide initial fixtures; a mocked alias test is not a host install. | Image built/pushed; real external host/catalog acceptance outstanding. |
| New `chaptarrng-bin` AUR, `slskdn/chaptarrng` COPR, `chaptarrng` Chocolatey | Fresh Arch, Fedora 44 (SELinux enforcing), Windows 2022 respectively. Resolve the **actual feed version and package hash** first; install and update from each feed, check service and paths, then rollback. The release workflow's recipe/package build jobs are useful build evidence, not proof of feed availability. | Confirm publication independently; installed v0.9.995 feed acceptance outstanding. |
| Old `bookshelfng` Debian package and Ubuntu PPA | Fresh Debian 13 and supported Ubuntu VM with systemd/apt and `.71` or other verified old package. Build exact-release candidate with `VERSION=0.9.995 ARCHIVE_PATH=<verified-linux-x64-tarball> OUTPUT_DIR=<new-dir> bash packaging/scripts/build-bookshelfng-deb-bridge.sh`; use `OLD_DEB`, `NEW_DEB`, `TASK_SCRATCH_DIR` with `packaging/scripts/test-bookshelfng-deb-roundtrip.sh` for its **mocked service** transaction. Then perform an actual apt installed service No/Manual/Yes/rollback cycle in the VM and a separate PPA delivery check if published. | Bridge candidate unpublished; synthetic round-trip and publish gate do not prove installed service or PPA delivery. |
| Old `bookshelfng-bin` AUR and `slskdn/bookshelfng` COPR | Fresh Arch and Fedora 44 VMs. Use `packaging/scripts/test-bookshelfng-aur-choice.sh` and `packaging/scripts/test-build-bookshelfng-rpm-bridge.sh` as fixture setup, then transact exact v0.9.995 packages with pacman/dnf, No/Manual/Yes, SELinux labels, health and rollback. Check old identity and saved data path. | Legacy recipes gated/unpublished; older-version acceptance is historical. |
| Old `bookshelfng` Chocolatey and Windows standalone installer | Fresh Windows 2022 x64 and x86 as applicable, verified `.76` predecessor. Use the Windows acceptance workflows and `integration/standalone-handoff/windows.py`; for Chocolatey test real `choco upgrade bookshelfng` with service settings, custom data path, PostgreSQL dump when configured, No/Manual/Yes, injected post-migration health failure, old package restoration and retry. Record feed delivery separately. | Standalone archives passed v0.9.995; Chocolatey identity bridge/feed and installer update need exact-current installed checks. |
| AppImage and Flatpak BookshelfNG IDs | Linux desktop with AppImage execution and Flatpak runtime/SDK 26.08, `appimagetool`, `flatpak-builder`. Build from verified Linux x64 archive using `bash packaging/scripts/build-bookshelf-desktop-candidates.sh <archive> <new-dir>`, then install the real outputs over old IDs, test persistent data, No/Manual/Yes, sandbox permissions and rollback. | Synthetic builder contract passed; no v0.9.995 installed desktop package acceptance. |
| Helm old OCI identity | Docker + Kind + Helm with separate namespace and PVC. Dispatch `.github/workflows/helm-handoff.yml` (`action=ci`, `runner_pool=public`) or reproduce pinned chart/image upgrade, Manual/Automatic, backup, health, rollback and retained PVC. Verify the actual OCI chart identity if published. | Historical installed fixture only; current publication gated. |
| Cloudron, Co-op Cloud, self-hosting catalogs, StartOS | Build candidate bundle using `VERSION=0.9.995 CHAPTARRNG_IMAGE_DIGEST=sha256:<real-published-index-digest> OUTPUT_DIR=<new-dir> bash packaging/scripts/build-bookshelf-container-platform-candidates.sh`. Test installed old identity on Cloudron 10.1.6; Swarm/Abra Co-op; actual catalog hosts; StartOS 0.4.0.3 x86_64 **and** aarch64 with official signed `.s9pk`. Exercise package delivery, persistent volumes, Manual/Automatic, health, backup and failed update/rollback. See platform READMEs under `packaging/legacy/`. | Builder's sentinel digest and older test-key VM rehearsals are **not** official signed/package-feed acceptance. |

For an isolated Linux glibc release archive check, after verifying both files,
run (use a *new* output directory):

```sh
python3 packaging/scripts/test-bookshelf-standalone-handoff.py \
  /task/BookshelfNG-v0.4.21.76-linux-x64.tar.gz \
  /task/ChaptarrNG-0.9.995-linux-x64.tar.gz \
  --output /task/evidence-linux-x64 \
  --candidate-revision c570d7524a07eacaee0920a6cb01ac2e63c6f80a \
  --runtime-id linux-x64
```

On Windows, use the corresponding `.zip` pair with
`python integration/standalone-handoff/windows.py <predecessor> <candidate>
--output <new-evidence-dir> --runtime-id win-x64 --candidate-revision
c570d7524a07eacaee0920a6cb01ac2e63c6f80a`. These archive harnesses
do **not** transact Chocolatey, RPM, Debian, AUR, AppImage, Flatpak, or a
platform catalog. For each of those, record a separate package-manager
transaction and source-data fingerprint.

Passing an installed bridge means the old package/service identity and
operator configuration remain intact, No cancels without mutation, Manual
defers conversion without altering the schema-158 source, Yes migrates and
serves `/ping` with a retained source backup, and an injected health failure
restores the old package/database and passes old-version health. Include an
independent anonymized operator snapshot with representative books, authors,
downloads and custom paths only with the operator's authorization. If a
publisher credential, official signed package or external catalog is absent,
record **blocked**, the exact missing dependency and the tested source
candidate; never mark that channel accepted or publish it to make the test
pass. Historical version evidence remains in the
[earlier channel matrix](BOOKSHELFNG_CHANNEL_ACCEPTANCE_2026-10-26.md).
