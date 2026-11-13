# ChaptarrNG PR #190 main sync and source inventory reconciliation

## Pins

- Common base before synchronization: `025498c1a9deb999a4acd1eafc4c807a252e0c29`
- PR head before synchronization: `f6e9cb4126da5c0a4280534702d2357f8a6aa007`
- `main` fetched for synchronization: `2df031b2e138e67d63182ff3d3fad0cde2a1cccf`
- The source inventory conflict was in `docs/localization/server-message-sources.json`.

The conflict was reconciled by retaining the PR inventory's 618 message records and source-bound localization wrappers, refreshing all callsite source-line hashes against the merged source tree, and carrying forward current-main callsites that remain live. The resulting checker report has no issues: 618 message records, 877 unique source callsites, 886 bindings, 12 direct locale catalogs, and one excluded dynamic-only template. The callsite match audit accounts for all current bindings through exact prior lines or explicit message IDs; it records zero source-text-only fallbacks.

Main changed two English messages. The existing 12 target values already match the corrected SABnzbd spelling and the revised Mailgun test-message wording, so this synchronization changed zero target catalog cells. `frontend/src/Utilities/Localization/server-messages.json` was refreshed from the reconciled source inventory.

The PR-side and main-side inventories, pin report, refresh script, result report, and validator output are retained in this directory. The standing workflow boundary is checked against the updated main after the merge is pushed.

No test suite, build, scan, CI, deployment, release, or tag was run or created. The server-message catalog checker is the repository's focused source/catalog consistency validator.
