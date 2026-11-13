# ChaptarrNG PR #190 review-gap input packet

Candidate-free exact-head input at `580538d38f92e0ec005366ff6bea3f2634400c2e` / tree `b61f7ca1f5b496c01a32ba7b8f3520076ec5cfc1`. Local branch `codex/chaptarrng-localization-complete-20261031` and its remote branch resolve to the same head. This packet includes current source and catalog targets only; it contains no proposed translations and makes no PR query or change.

## Selected cells

- Source positions 654 (`server.message.m783307436ce0`) and 695 (`server.message.m843e64bf5198`): all 12 locales each, 24 selected cells, pinned to corrected English source hashes and current production caller snapshots. Their earlier locale review source pins are stale; the source-correction record is included.
- Seven changed existing cells without exact target-hash review evidence: `hi:MqttGatewayPublishHomeAssistantDiscovery`, `hi:notification.heading.renamed`, `id:notification.field.links`, `ja:notification.sensor.missingBooks`, `ko:notification.sensor.health`, `zh-Hans:notification.heading.renamed`, and `zh-Hant:notification.heading.renamed`.
- All 12 locale values are included as context for each of the seven source IDs, for 84 locale snapshots total. The remaining context-only rows are clearly marked in `locale-context-cells.jsonl`; the selection manifest lists exactly 31 cells.

## Files

- `manifest.json`: selected cell IDs/locales, exact source/current-target/catalog hashes, and pin set.
- `selected-cells.jsonl`: hash-only list of 31 review selections.
- `source-cells.jsonl`: current English source text and hashes, plus corrected-source ancestry pins.
- `locale-context-cells.jsonl`: current target text/hash and catalog file pins for 84 rows; no candidates.
- `caller-snapshots.jsonl`: current production caller lines and neighboring context with registry/file hashes.
- `active-hold-caller-status.json`: caller-existence check for the 61 held cells; no hold was released.
- `attestation.json`: local/remote exact-head pins and clean worktree state.
- `build_packet.py`: reproducible packet builder.
