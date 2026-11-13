# ChaptarrNG PR #190 Core W300–W349 primary review

Pinned source: `f0082d1b655c05b8d4019ede523dd695cd6d745a` / tree `4cf2322354e9cf9b12d59cf10d0d8661c68ab4af`. The review covers 50 source keys × 12 locales = 600 cells. It used only the sealed candidate-free packet and direct caller context at this exact head.

The primary ledger contains 87 proposed corrections, 465 accepted-current cells, and 48 hash-only callerless holds across four keys. No target changes are recommended for callerless keys without verified production context. Recommendations remain pending native-speaker review and have not been applied.

Prior lineage through W250–W299 is hash-only: W0–W199 has 1,519 reattested rows including 312 preserved holds; W200–W249 has 600 rows including 12 preserved holds; W250–W299 has 600 final readbacks, 42 applied changes and 558 preserved-current cells. The separate Indonesian root adjudication is attested by its exact SHA-256 in the candidate-free packet.

No W300–W349 blind or cross-review outputs were accessed. A prior W250–W299 omnibus checksum operation inadvertently hashed that earlier packet’s cross-review files; only filenames and checksum status were shown, their contents were not reviewed, and the prior cross results were not used. The exposure is disclosed in `review-process-exposure.json`. The candidate-free packet records live main/base drift and caller-path overlap. No product catalog or PR state was modified; no tests, builds, security scans, CI jobs, or workflow changes were run.
