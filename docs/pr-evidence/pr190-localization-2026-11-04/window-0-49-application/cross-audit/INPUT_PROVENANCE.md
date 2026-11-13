# Input provenance

The bundle includes the exact primary and blind packets used for this review under `input/`.

- `input/candidate-primary/SHA256SUMS` passed before review and after copying.
- `input/blind/SHA256SUMS.txt` passed before review and after copying.
- `input/blind/input/SHA256SUMS.txt` passed before review and after copying.
- The candidate-free source packet and caller context resolve to the pinned ChaptarrNG checkout in `source-pin.json`; all 600 source/current values and all 50 caller-context records (71 caller references) were checked against that exact checkout.
- The candidate-free-only reviewer workpaper is `work/reviewer-a.jsonl` and covers only ordinals 0–24.

`verify_cross_audit.py` rechecks the bundled packet manifests and all ledger links. With `--source-worktree`, it also rechecks the checkout head/tree/clean state, source and locale catalog values, and caller file/line hashes.
