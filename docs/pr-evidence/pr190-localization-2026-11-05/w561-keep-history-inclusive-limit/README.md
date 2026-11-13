# ChaptarrNG PR #190 W561 inclusive KeepHistory limit

The pinned NzbGet validation rejects `value > 25000`, so exactly `25000` is accepted. The old wording said “less than 25000”; the reviewed source text now says “must not exceed 25000” and uses source ID `server.message.m3a79390fb21e`.

Product commit [`9b6c2d65e843623aabf1b02f57eb0408bd3734f7`](https://github.com/snapetech-org/chaptarrng/commit/9b6c2d65e843623aabf1b02f57eb0408bd3734f7) changes the English message, source registry/hash snapshot, caller key, and all 12 target locales while preserving the predicate. The exact 13-catalog readback and the 12-locale root adjudication pass.

Primary, independent blind, cross-review, and root evidence is in the sibling directories. Their pinned review input is commit `c01c3974a01dfcab6a1aa09401c66d412bc88e60` / tree `55ea7696f4981fc56a774f38be477f89e454a7a3`; product application followed in commit `9b6c2d65e843623aabf1b02f57eb0408bd3734f7`. The portable verifiers read the pinned Git objects and committed evidence files, so they do not depend on the original temporary worktree or scratch paths.

Run these from this directory or any directory in a clone containing the pinned commits:

```sh
python3 -B verify_product_readback.py
python3 -B root-adjudication/verify_root_adjudication.py
python3 -B cross-review/verify_cross_review.py
```

Machine-review confidence is moderate. No native-speaker approval or exact-head product-browser acceptance is claimed. No tests, builds, scans, CI dispatches, deployments, merges, releases, or tags were performed for this correction.
