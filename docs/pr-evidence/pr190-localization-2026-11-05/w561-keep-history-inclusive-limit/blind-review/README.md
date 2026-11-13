# ChaptarrNG W561 independent blind review

Pinned source/caller review at Git commit `c01c3974a01dfcab6a1aa09401c66d412bc88e60` / tree `55ea7696f4981fc56a774f38be477f89e454a7a3`. The current key is `server.message.m453c42aa8de5`; the prospective corrected message uses `server.message.m3a79390fb21e`. The review records both IDs and binds caller evidence to the pinned code.

The caller rejects only `value > 25000`; exactly 25000 is permitted. Current English and all 12 target values say “less than 25000,” which excludes that allowed boundary. The ledger proposes inclusive-maximum wording in all 12 target locales and verifies exact preservation of `NzbGet`, `KeepHistory`, and `25000`.

This is machine semantic/token review with moderate confidence. No native-speaker review or approval was performed. The primary packet was not opened or used. No repository files were edited; no tests, builds, scans, or CI were run.

Run `python3 -B verify_packet.py` from this directory to validate the source pin, caller evidence, locale inputs, proposals, and checksums. It reads the exact pinned Git object and does not require the original scratch worktree.
