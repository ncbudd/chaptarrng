# ChaptarrNG PR #190 W450-W499 primary review

This sealed primary review covers 600 candidate-free cells (50 source keys × 12 locales) at PR head `16c809b4787d70616a1a296ab0d90cf17923ba86`, tree `dbd8343a42476f4e830428cc59efb7f4830251d5`. It uses only the fresh candidate-free packet and its caller context.

`ledger.jsonl` records each cell, decision, exact source/current hashes, context hash, caller/catalog file pins, token checks, confidence, and rationale. `proposals.jsonl` contains recommended corrections/refinements. `holds.jsonl` has 48 callerless hash-only holds with no source key, locale, or text. The two numeric flags for Octal rendered as 8進数/8진수 are retained and manually assessed.

Run `python3 verify_primary.py` for portable structure and checksum verification. To bind the packet to the candidate-free source rows and caller contexts, run `python3 verify_primary.py --input ../candidate-free/input`.
