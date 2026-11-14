# Standalone archive builds

ChaptarrNG's source release matrix targets the ten runtime identifiers used by
the final BookshelfNG archive workflow:

| Runtime identifiers | Runtime pack source |
| --- | --- |
| `linux-x64`, `linux-arm64`, `linux-musl-x64`, `linux-musl-arm64`, `osx-x64`, `osx-arm64`, `win-x64`, `win-x86` | .NET 10 SDK 10.0.404 |
| `linux-x86`, `freebsd-x64` | Pinned .NET 10 runtime packs built by `packaging/scripts/build-extra-platform-runtime-packs.sh` |

## Validate without publishing

`.github/workflows/standalone-asset-validation.yml` builds the UI once, builds
all ten self-contained archives, verifies each archive and checksum, and
stores temporary build products only on the GitHub runner. It uses version
`0.0.0` and does not create a GitHub release, package, image, installer, or
update-channel handoff. The exact-head result must pass before these candidate
assets can be considered for a future release.

## Build the custom runtime packs

The Linux x86 and FreeBSD build uses Docker, .NET SDK `10.0.115` for the runtime
and ASP.NET source builds, SDK `10.0.404` for ChaptarrNG, and the pinned
`v10.0.15` runtime and ASP.NET source. FreeBSD packs are built from the .NET VMR
tag `v10.0.115` at commit
`8e0f8ed2312954727f8919d7d1c2f78b483b4ee7` in the pinned Azure Linux 3.0
FreeBSD cross-build image recorded in
`packaging/scripts/build-extra-platform-runtime-packs.sh`. Before cloning the
large VMR tree, the script verifies over HTTPS that the immutable pinned commit
contains .NET and ASP.NET Core 10.0.15 source-version markers. The source build
must then generate the required FreeBSD runtime packages and archive; each
generated package version and runtime archive is checked before the output is
assembled. The script does not consume the obsolete `v10.0.113` archive or
pretend that prebuilt upstream FreeBSD package assets exist. The output contains
a source and image record plus SHA-256 values for each package and runtime
archive. Native installed acceptance is still required before publishing a
FreeBSD archive. Use two unique, absolute, task-scoped directories that do not
already exist:

```sh
DOTNETVERSION=10.0.404 \
PLATFORM_RUNTIME_WORK_DIR=/tmp/chaptarrng-platform-runtime-work-task-id \
PLATFORM_RUNTIME_PACKS_OUTPUT=/tmp/chaptarrng-platform-runtime-packs-task-id \
bash packaging/scripts/build-extra-platform-runtime-packs.sh
```

The work directory contains the pinned VMR checkout, cloned .NET source trees,
and build outputs. The output directory contains runtime packages, SDK
metadata, source provenance, SHA-256 values, and the install helper. Keep those
paths separate from user data and remove only the exact task-scoped paths after
their consumers finish.

The SDK's reference packs can have a newer servicing version than the pinned
runtime sources. The pack builder copies the SDK's installed reference-pack
versions, while the Linux x86 and FreeBSD standalone publish explicitly targets
runtime `10.0.15` to match the custom runtime packages.

The runtime-pack installer merges files into the SDK already installed on the
runner. It preserves file modes and symlinks but deliberately does not restore
ownership or source timestamps, which may be unsupported for shared SDK files.
`packaging/scripts/test-install-extra-platform-runtime-packs.sh` covers an
overlapping pack file so the copy path is checked against a preexisting SDK.

## Build a standalone archive

Build the frontend first so `_output/UI/index.html` exists. The archive builder
requires .NET SDK `10.0.404` and an output directory.
For Linux x86 and FreeBSD, download or build the custom runtime-pack artifact,
then set `CUSTOM_RUNTIME_PACKS_DIR` to its `packages` directory:

```sh
CUSTOM_RUNTIME_PACKS_DIR=/path/to/platform-runtime-packs/packages \
DOTNETVERSION=10.0.404 \
bash packaging/scripts/build-standalone.sh 0.0.0 freebsd-x64 /path/to/task-output
```

The builder creates a `.tar.gz` or `.zip` archive and a `.sha256` sidecar in
the requested output directory. Its temporary bundle is created with
`mktemp` under `${TMPDIR:-/tmp}` and removed by an exit trap.

macOS and FreeBSD archives include
`scripts/bookshelfng-standalone-launch.sh` and the shared handoff supervisor.
Use that launcher with the existing BookshelfNG data directory for an optional
terminal `[y/N]` choice; it defaults to Manual when no terminal is attached.
The supervisor stages the migration, retains the source for rollback, checks
startup health, and restores the source if the handoff fails. The launcher does
not change the old service or local launcher path; switch it after the new
service passes health. On FreeBSD, install the `sqlite3`, `icu`, `libunwind`,
and `libinotify` runtime packages before starting the archive:

```sh
pkg install --yes sqlite3 icu libunwind libinotify
```

The application needs `sqlite3`; the .NET runtime needs ICU, libunwind,
libinotify, and MIT Kerberos. Before starting the archive, install `krb5` or
`krb5-122` version 1.22.3 or newer; earlier versions are affected by the
[FreeBSD krb5 security advisory](https://vuxml.freebsd.org/freebsd/8dc02503-dd51-11f1-a654-f8b46a88f42c.html).
If the configured package repository offers an older version, update it or
build and install the updated
[FreeBSD krb5-122 port](https://cgit.freebsd.org/ports/tree/security/krb5-122).
Run `pkg audit -F` after installing the dependencies.
These dependencies are also listed in the
[.NET FreeBSD runtime requirements](https://github.com/dotnet/runtime/blob/main/docs/workflow/requirements/freebsd-requirements.md).
The launcher links the bundle's SQLite dependency to the installed library and
selects a compatible installed OpenSSL ABI when needed.

## Publication gate

ChaptarrNG `v0.9.995` published all ten standalone archives with SHA-256 and
Sigstore sidecars. Installed migration and forced rollback passed on the nine
Linux, macOS and Windows runtime targets; the current FreeBSD archive still
needs native installed acceptance. The BookshelfNG identity bridge remains
unpublished. See the [package acceptance handoff](../maintainers/PACKAGE_ACCEPTANCE_HANDOFF_2026-11-10.md)
for current evidence and platform-specific outstanding checks.

The local `0.9.1001` FreeBSD x64 candidate built with the `.NET 10.0.15`
runtime packs passed installed handoff on FreeBSD 15.1-RELEASE-p6 amd64. The
candidate archive SHA-256 is
`e87ec939211a4737fe400b9ec59d0218ab96f83740db8338ff52ad29bffa580d`; the
pinned BookshelfNG `.76` predecessor SHA-256 is
`129fb321342e9bfe36a26429e138f88380ee5429e81f84a75a6f4488894cba89`. No,
headless Manual, Yes with health and retained source backup, and forced-health-
failure rollback all passed. Evidence is retained at
`/mnt/disks/scratch/chaptarrng-backlog-release-20261112/freebsd-evidence-current-source-20261113/evidence-pass1`.
This archive came from a dirty local tree (`HEAD=73d145a`, `MERGE_HEAD=d066e65`,
index tree `f51fa91`); repeat acceptance against the exact committed release
head before publication. This does not change the historical v0.9.995 result
above.
