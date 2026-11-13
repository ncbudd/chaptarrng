# ChaptarrNG PR #190 W561 third-party cross-review

The primary and independent-blind packets both pass their input verifiers and checksum checks at head `c01c3974a01dfcab6a1aa09401c66d412bc88e60` / tree `55ea7696f4981fc56a774f38be477f89e454a7a3`. The exact caller at `src/NzbDrone.Core/Download/Clients/Nzbget/Nzbget.cs:348` rejects `value > 25000`; therefore 25000 itself is allowed. The proposed English “NzbGet setting KeepHistory must not exceed 25000” corrects the existing strict wording.

The cross-review selected the source/catalog key transition from `server.message.m453c42aa8de5` to `server.message.m3a79390fb21e` and 12 locale target corrections. Primary and blind targets agree exactly in 5 locales and differ in 7; the ledger records the choice and rationale for every locale. All final targets preserve `NzbGet`, `KeepHistory`, and `25000`. Language confidence is moderate; no native-speaker approval was performed.

The product application is recorded separately in the enclosing packet README and commit binding. The verifier reads committed primary/blind evidence and the exact pinned Git object; it does not require the original scratch paths or worktree. Run `python3 -B verify_cross_review.py` to verify the packet.
