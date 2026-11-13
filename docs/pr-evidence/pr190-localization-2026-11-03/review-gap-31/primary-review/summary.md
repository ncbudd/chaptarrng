# Review summary

- Scope: 31 selected cells across 7 source IDs and 12 locales. The 53 context-only rows were used only for consistency context and are not included as decisions.
- Exact packet pin: PR #190 candidate-free head `580538d38f92e0ec005366ff6bea3f2634400c2e`, tree `b61f7ca1f5b496c01a32ba7b8f3520076ec5cfc1`. The packet attests that its local and remote branch heads agree and the worktree was clean.
- Source corrections: ranks 654 and 695 were reviewed against the corrected English source hashes and caller snapshots. Both correction pins match the live source hashes in the packet. Current targets preserve the corrected meanings: “Disable the 'Check before download' option in SABnzbd.” and “Unable to send a test message through Mailgun.”
- Decisions: {'accept-current': 31}. No target text changes are proposed; each recommended target is exactly the current target.
- Selection reasons: {'source-pin-recheck': 24, 'changed-existing-target-without-exact-review-hash': 7}.
- Confidence: {'high': 29, 'moderate': 2}. Moderate confidence marks the Hindi technical loanword and Japanese sensor-label nuance; both are accepted as semantically adequate.

## Review basis

The two server messages were assessed against their exact English source text and production caller snapshots. The other selected labels were assessed against their source labels and the packet's caller context: a Home Assistant checkbox, Discord/Slack notification headings, a Discord links field, and MQTT sensor labels. Cross-locale rows were read as consistency context only; no context-only cell was promoted into the selection.

All 31 entries in `per-cell-ledger.jsonl` include exact current and recommended targets, SHA-256 hashes, rationale, confidence, placeholder checks, protected-literal checks, and caller/source evidence pins. For every row, current and recommended target hashes are identical.
