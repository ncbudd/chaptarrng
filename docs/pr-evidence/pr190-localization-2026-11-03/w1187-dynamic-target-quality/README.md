# ChaptarrNG PR #190 — W1187 dynamic target-quality message

Exact-head review and application at `c7e95620c2a89646eb6a37c7e35441804b4911bb` / tree `78c7aa519cbe3ed7874b2f93b6976237b7d336e9`. The earlier W1150–W1199 packet held all 12 cells because it treated `M4B` as a fixed protected literal. Two new independent reviews checked the source template, dynamic parameter, both exact production callsites, and all locale cells. One reviewer saw only aggregate W1150–W1199 counts in the PR body before sealing; the second queried head/status only and did not read the PR body or prior packets.

The callsites pass `TargetQualityName ?? "M4B"` as dynamic `{value0}`. `M4B` therefore reaches the message through the placeholder when the setting is absent; it is not fixed catalog text. Root adjudication accepts nine current cells and applies one German correction and French/Vietnamese refinements. All 12 retain exactly one `{value0}`. It also clears the erroneous `protectedLiterals: ["M4B"]` registry annotation; the English source ID/text and source fingerprint remain unchanged. The exact-hash plan, root ledger, both independent reviews, registry correction, and readback are retained here.

This is machine-assisted review; native-speaker approval is not claimed. Exact-head browser review remains outstanding because no deployment exists for this PR head. No tests, builds, scans, CI, workflow edits, releases, or tags were made.

See `EVIDENCE-SHA256SUMS.txt` for whole-tree checksums.
