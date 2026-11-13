# ChaptarrNG PR #190 cross-review: W450–W474

This part covers Core source ordinals 450–474 across all 12 locales: 300 cells total. The PR head/tree are `16c809b4787d70616a1a296ab0d90cf17923ba86` / `dbd8343a42476f4e830428cc59efb7f4830251d5`; the API base is `025498c1a9deb999a4acd1eafc4c807a252e0c29`. Live main had advanced from the candidate-free seal and is recorded at entry and exit; cross rows remain bound to the pinned PR head and base.

`ledger.jsonl` contains all 276 caller-backed cells with current targets, exact primary/blind proposal targets where present, the cross decision, recommended wording, rationale, caller/catalog pins, and token checks. `holds.jsonl` contains the remaining 24 cells at ordinals 469 and 474 as text-free hash-only holds. It includes no source keys or source, current-target, or proposal text for those holds.

The reviewer reverified the candidate-free input, primary and blind packet checksums and verifiers, then rebound all 300 selected candidate-free row hashes to both review ledgers. The PR API base/head/tree remained unchanged from entry to exit while live main advanced from `73515010a360d64248c54bc51ebd66c6d50344a8` to `2ade9a5280a64ce7de8f1016961f88e93bd6cb8e`. The two octal terms in Japanese and Korean use the conventional numeral-bearing technical notation `8進数` / `8진수`; the numeric heuristic is recorded as a lexicalized-token exception, not a permission-value change.

Run the portable verifier from this directory:

```sh
python3 verify_cross_review.py
```

It defaults to the sibling candidate-free, primary and blind input packets; optional `--candidate-free`, `--primary`, and `--blind` arguments can point to those packet directories elsewhere. The checksum list covers all part files except itself. No repository, catalog, workflow, or PR edits were made.
