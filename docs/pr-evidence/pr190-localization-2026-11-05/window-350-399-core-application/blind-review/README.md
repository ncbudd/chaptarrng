# W350–W399 blind review seal

This directory contains a 600-cell independent blind review for the pinned candidate-free packet. It is bound to PR #190 head `dbe530c9d1a7fd2c12ce2aef76ec74c5c2188aa0` and tree `be10d71209076f753ef295038a9f3c3646a918a3`.

`ledger.jsonl` contains one row per English source key and locale. Each row records the exact current source and target values and hashes, catalog pins, caller-context fingerprint, placeholder/numeric/markup summaries, status, confidence, rationale, and any exact proposed target and hash. `caller-context-review.jsonl` retains the complete candidate-free caller records with a reviewer note for each source key.

The blind seal records that no primary packet or proposal files were opened before ledger completion. The review used only the candidate-free packet and makes no native-speaker claim.

Verify from this directory with:

```sh
python3 verify_blind_ledger.py
```

When copying this directory elsewhere, pass the candidate-free input path explicitly:

```sh
python3 verify_blind_ledger.py --input /path/to/candidate-free/input
```

`SHA256SUMS.txt` pins the portable output artifacts; the verifier checks both that list and the candidate-free packet's own `SHA256SUMS.txt`.
