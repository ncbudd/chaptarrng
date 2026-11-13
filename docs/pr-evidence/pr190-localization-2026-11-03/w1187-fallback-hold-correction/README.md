# ChaptarrNG PR #190 W1187 fallback-hold correction

This evidence packet records the source-bound re-review of source ordinal 1187 (`server.message.md764ed5e74b4`) at PR head `00d37b25ce5534135c2dacaf6a84d9d15fe0bb0b`, tree `13e57e7826db4db86556f244fb066e4915022511`. The exact source registry and both `ConversionJobService.cs` call sites show that `M4B` is the caller's null fallback passed as dynamic `{value0}`. `protectedLiterals` is empty. The earlier hold treated `M4B` as protected source text; that premise was false.

The independent review accepts all 12 existing locale values and clears all 12 carried holds. Plan: 12 `accept-current` no-ops, zero updates, zero new holds. Nine values still match the former hold targets; German, French, and Vietnamese already match later applied exact-hash resolutions. No catalog value is changed by this evidence commit.

The packet contains the candidate-free input, blind review, cross-audit ledger, exact source/caller/catalog pins, prior-hold reattestation, apply plan, and portable application verifier. The original cross-audit was verified against the pinned base head before this evidence-only commit. Qualified native-speaker review and exact-head headed-browser review remain pending. No tests, builds, CI, workflow edits, merges, releases, or tags were performed.

Run `python3 docs/pr-evidence/pr190-localization-2026-11-03/w1187-fallback-hold-correction/verify_hold_reclassification.py` from the repository root after the commit is pushed. The nested cross-audit and blind packets are immutable reviews of the pinned base head; their live-ref attestations record that review-time head.
