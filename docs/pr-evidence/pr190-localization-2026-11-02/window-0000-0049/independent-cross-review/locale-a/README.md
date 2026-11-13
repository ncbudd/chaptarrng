# ChaptarrNG PR #190 W0–49 locale cross-review

- Scope: locales `ar`, `de`, `es`, `fr`, `hi`, and `id` (300 cells; 50 keys per locale).
- Review checkout: `7bb2b2f977e81d214318b3f873afe8ab17f03ed5` (tree `5fdb46e8b55083b44f6ca109b1e46fd5b375b7cb`).
- Primary input: `primary-decisions.jsonl` from the specified W0–49 packet.
- Integrity checks: all 300 source/current-target values and hashes match the checkout catalogs; all 804 caller references match their re-attested current source lines and file hashes; all primary candidate hashes validate.
- Dispositions: accepted 290, missed 8, refined 2, held 0, noop 0.
- Every replacement has an exact UTF-8 SHA-256 in `proposedTargetSha256`; unchanged accepted rows omit `proposedTarget`. Original row fields are retained.
- Native speaker approval: false, as supplied.
- Blockers: none. This was a read-only review; no repository changes, tests, builds, scans, CI, or releases were run.

`SHA256SUMS` covers this README and `crossreview-decisions.jsonl`.
