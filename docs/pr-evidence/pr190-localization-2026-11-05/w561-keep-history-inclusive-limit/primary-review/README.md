# ChaptarrNG W561 NzbGet KeepHistory message review

Pinned to Git commit `c01c3974a01dfcab6a1aa09401c66d412bc88e60` / tree `55ea7696f4981fc56a774f38be477f89e454a7a3`. The current English key is `server.message.m453c42aa8de5` (“NzbGet setting KeepHistory should be less than 25000”). The proposed text “NzbGet setting KeepHistory must not exceed 25000” hashes to `3a79390fb21e5a7e7e4ea479d3d5f2643862a645f76312b3f107817fde29c5b4` and source key `server.message.m3a79390fb21e`.

The exact validation at `src/NzbDrone.Core/Download/Clients/Nzbget/Nzbget.cs:348-350` rejects `value > 25000`; it accepts `value == 25000`. I accept the proposed “must not exceed 25000” wording because it preserves that inclusive boundary. The old “less than 25000” wording wrongly excludes 25000.

`locale-translations.jsonl` contains one proposed concise translation for each direct locale, its old target and hash, the proposed target and hash, rationale, confidence, source ID, and caller-file/context pins. All targets preserve `NzbGet`, `KeepHistory`, and `25000`. Confidence is moderate for locale wording. These are proposed corrections, not native-speaker approval.

The verifier reads the pinned Git object and this committed evidence directory; it does not require the original scratch worktree. Verify with `python3 -B verify_primary_review.py`.
