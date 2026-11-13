# W450–W499 exact-hash application

`apply-plan.json` binds 111 root-adjudicated edits to the exact W450–W499 input head, candidate-free rows, cross-review, independent second opinion, and root decisions. `apply_exact_hash_plan.py` accepts only the pinned source tree and current catalog hashes; it changes values in the 12 direct locale catalogs without changing catalog shape.

The product change is commit `fb9d0439f5adf751b07c5d6167009591d0b0c6e7` (tree `f8ee83c8a65b1a09fd477cea56c9d8c47b1c2ea2`). `verify_application.py` reads back all 600 cells against that commit and its exact parent. The readback confirms 111 applied targets, 441 unchanged caller-backed cells, and 48 unchanged hash-only holds; each catalog retains 4,165 keys and its original key order, non-target values are unchanged, and English is byte-identical.

The Japanese and Korean octal terms have explicit lexicalized-number exceptions. No held target text is written to the readback. This is catalog evidence, not a test suite or native-speaker/browser signoff.
