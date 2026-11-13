# Readback evidence

`application-verification.json`, `all-cell-readback.jsonl`, and `catalog-readback.json` record the exact-hash application at product commit `7e69f46e21f1ea7455893179116ec85ee2b0f85e`. The final `current-head-*` files were regenerated from `verify_current_head.py` at integration head `4688c998d92c821bbc1464ea4640c90615a69327`, comparing against live main `beb4f9550ec3340b3f6d9b34c721055610e68847`. The verifier checks all 600 target cells, all 50 caller contexts, source text hashes, exact catalog key counts/order, product commit paths, and the current sealed 4688 review.

Packet verifier/checksum results are in `packet-verification-results.json`. No tests, builds, or scans are represented by these readback verifiers.
