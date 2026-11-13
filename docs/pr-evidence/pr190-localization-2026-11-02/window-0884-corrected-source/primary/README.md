# ChaptarrNG PR #190 corrected-source review: ordinal 884

This primary packet reviews the 12 locale cells for stable ID `server.message.mf00d6bc38ae8` after the English source correction was pushed. It is pinned to OPEN/DRAFT PR head `722c0aaab4eda88bb507ba4a165e2f6bb22901fa`, tree `d162735f61d934389634111229b42beae04aaeea`. All seven localization PR heads were recorded before and after review.

The corrected source is `Can not contain '\', '//', or start/end with '/'`. Four QBittorrent settings validation rules use the same regex and stable message ID. The regex forbids backslash anywhere, repeated `//`, and a leading or trailing `/`. All 12 current locale values still omit the literal backslash. Eleven locales receive concrete correction proposals that preserve all three constraints. Hindi remains held because I cannot confidently approve a fluent correction; its final target is null.

`locale-review.jsonl` records exact source, current, proposed/final hashes, source/caller/catalog pins, prior hold status, and structural and semantic checks per locale. `source-caller-reattestation.json` records the source correction metadata and four caller line pins. The former W850 hold/readback is historical context only; current values were read from the exact current catalog files.

No repo or PR edits, tests, builds, CI, or browser actions were performed. This is machine-assisted primary review, not native-speaker approval; native-speaker review remains outstanding.

## Files

- `live-heads-before.json` / `live-heads-after.json`: all seven live PR head snapshots and exact ChaptarrNG ref/tree/worktree checks.
- `source-caller-reattestation.json`: exact source and caller metadata/hashes.
- `locale-review.jsonl`: 12 per-locale decisions and final targets.
- `summary.json`: scope, counts, and caveats.
- `SHA256SUMS.txt`: checksums for packet files.
