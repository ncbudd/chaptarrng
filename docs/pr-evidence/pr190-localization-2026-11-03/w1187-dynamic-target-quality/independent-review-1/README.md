# Independent W1187 semantic review

- Repository / PR: `snapetech-org/chaptarrng` #190
- Live PR state at requery (2026-11-03 01:43 UTC): OPEN, draft
- Exact head/tree: `c7e95620c2a89646eb6a37c7e35441804b4911bb` / `78c7aa519cbe3ed7874b2f93b6976237b7d336e9`
- Reviewed source: `server.message.md764ed5e74b4` across 12 direct locales
- Dispositions: 9 accept-current, 3 corrections, 0 holds
- Native-speaker approval: not claimed

## Decision

`TargetQualityName` is dynamic data carried by `{value0}`. Both cancellation callsites use the configured target name with fallback `M4B`; therefore the fallback appears through `{value0}` when no configured name is supplied. A fixed `M4B` in a translation is unnecessary and becomes incorrect when the configured name differs. The source registry's `protectedLiterals: ["M4B"]` looks inconsistent with the source template and pattern, which contain no literal `M4B`.

Recommended exact targets:

- German: `Die {value0}-Konvertierung wurde abgebrochen.`
- French: `La conversion {value0} a été annulée.`
- Vietnamese: `Quá trình chuyển đổi sang {value0} đã bị hủy.`

Other current values are accepted. All current and proposed targets preserve exactly one `{value0}`.

## Process limitation

Before sealing, an initial live PR fetch exposed the PR body, and I read its aggregate W1150–W1199 milestone summary. It did not contain a W1187-specific candidate, disposition, target, or hold. I did not open prior review packets or READMEs and did not use the aggregate summary in these cell decisions. This limits the claim of a fully blind process and is recorded in `review.json` and `seal.json`.

No repository/catalog/PR/workflow files were edited. No tests, builds, scans, CI, browser work, or native-speaker review were run.
