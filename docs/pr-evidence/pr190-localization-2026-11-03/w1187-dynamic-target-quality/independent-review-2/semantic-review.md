# Independent exact-cell semantic review — ChaptarrNG PR #190

- Date: 2026-11-02
- Scope: `server.message.md764ed5e74b4` at commit `c7e95620c2a89646eb6a37c7e35441804b4911bb`, tree `78c7aa519cbe3ed7874b2f93b6976237b7d336e9`.
- PR state snapshot: open, draft. The GraphQL query requested only state, draft flag, head commit and tree; it did not request or read the PR body.
- Source: `{value0} conversion was cancelled.`; SHA-256 UTF-8: `d764ed5e74b487042e8b1b9584e9e3bf5728ac982328afddc95651da24621b64`.
- Source template: `{TargetQualityName} conversion was cancelled.`; parameter `{value0}` is the dynamic `TargetQualityName`.

## Runtime evidence

The conversion request sets `TargetQualityName` from `convertedQuality.Quality.Name` in `src/NzbDrone.Core/MediaFiles/BookImport/ImportApprovedBooks.cs:2498`. Both pinned cancellation callsites are in `src/NzbDrone.Core/MediaFiles/ConversionJobService.cs`: line 195 uses `job.TargetQualityName ?? "M4B"`; line 603 uses `request.TargetQualityName ?? "M4B"`. Their catalogued source-line SHA-256 values were verified against the exact checked-out lines: `8c6b4ea5b8dc186855cb06ec101976b7ee8c90364cce42f5d2b4f594034d6806` and `e60a2173817aeea3829f7590963e82994d2bc0e6ecce3ca48429c02a442bef37`.

On the cancellation path, `QueueStatusCell` sends `conversionMessage` through `translateServerMessage`. The matcher captures the variable target-quality name as `value0`; translation interpolates that value and adds bidi isolates around dynamic strings. `M4B` is a null fallback and can be the dynamic value itself, so it should not be hardcoded as a universal prefix.

## Cell-by-cell review

`Current` strings and SHA-256 values are copied from the 12 locale core catalogs at the exact head. `Proposal` hashes cover the exact proposed UTF-8 strings. “Provisionally accept” is this review recommendation, not native-speaker approval.

| Locale | Current value | Current SHA-256 (UTF-8) | Recommendation / proposal | Confidence |
|---|---|---|---|---|
| `ar` | `تم إلغاء تحويل {value0}.` | `04a80a98b60ecde8ee1b1c64d7c6843f16d236de8268d135ce2796d60ddd1931` | provisionally accept current | moderate |
| `de` | `M4B-Konvertierung von {value0} wurde abgebrochen.` | `0b1aa08ee42c2bc060a7c408ea3ff333bcb9f415c78b6186e3fa233d4e2ecae5` | propose_correction: `Die Konvertierung zu {value0} wurde abgebrochen.` (proposal SHA-256 `2fd7cb5ff9e4a7bc19b8bba32485ffa8a24a74635a849f82e79b3c7c1462083a`) | high |
| `es` | `La conversión {value0} fue cancelada.` | `0838c73941fa1e8ecd01bc7e61dc6069a50436e47419c24b8bb7ec64ce03476d` | provisionally accept current | moderate |
| `fr` | `{value0} conversion a été annulée.` | `ee2a084b2bfd207c139a52fe280e6ae16c5387d27cff0df198209428ed6673fe` | propose_clarifying_revision: `La conversion vers {value0} a été annulée.` (proposal SHA-256 `e6d14b91ccc9eddfc0769d4634e4e907f8a448efafff8c5f00978894a9e468f9`) | moderate |
| `hi` | `{value0} रूपांतरण रद्द कर दिया गया है।` | `3961f0fc1b50a6849fe8935a84bd77891f70145cba3a0add4dd3cced23c33e03` | provisionally accept current | moderate |
| `id` | `Konversi {value0} dibatalkan.` | `2be6a163eed58c7a310da047fe3cf063841392e777a6bbecec2c7898939e2b0d` | provisionally accept current | moderate |
| `ja` | `{value0}の変換がキャンセルされました。` | `7f0bfaba4a95fdf1fcc80fb776fa6ab8edcfd0e30318a2ce1c21c93cd76ad6b4` | provisionally accept current | moderate |
| `ko` | `{value0} 변환이 취소되었습니다.` | `917c293100a0bb5f135086faf16c9526a008799d4b04a633b5e9499d0c7d22f2` | provisionally accept current | moderate |
| `pt_BR` | `A conversão {value0} foi cancelada.` | `32d9b0a23784b91cece2b5f47cfd925f9439173abc345b831a5b3ff5f5fa0dcb` | provisionally accept current | moderate |
| `vi` | `{value0} chuyển đổi đã bị hủy.` | `03716ae2adc9a1a4debe4499cff05f123c69d35f3575eab7edfdb2b72b7121dd` | propose_clarifying_revision: `Quá trình chuyển đổi sang {value0} đã bị hủy.` (proposal SHA-256 `7982e77996746f7091385da5939d5debe6a9883f18413cf821f579c66fe5f518`) | low |
| `zh_CN` | `{value0} 转换已被取消。` | `428a97403101ff42db7137e97c4a6e914db6de798d325a0dab840f3b5d31d912` | provisionally accept current | moderate |
| `zh_TW` | `{value0} 轉換已被取消。` | `ec26cd8399e1cfde4f08dfee6a38691b2c911dc50f0381c91b859d5d5c21c024` | provisionally accept current | moderate |

## Findings

- **German — propose correction (high confidence).** Current `M4B-Konvertierung von {value0} wurde abgebrochen.` hardcodes M4B and makes the dynamic target quality read like the input/object of an M4B conversion. Proposal: `Die Konvertierung zu {value0} wurde abgebrochen.` This says the conversion to the dynamic target quality was aborted. The current and proposed values each contain `{value0}` once.
- **French — propose clarifying revision (moderate confidence).** Current `{value0} conversion a été annulée.` follows English word order. Proposal: `La conversion vers {value0} a été annulée.` The current intent is inferable; the proposal states the target direction more clearly.
- **Vietnamese — propose clarifying revision (low confidence).** Current `{value0} chuyển đổi đã bị hủy.` is difficult to parse naturally. Proposal: `Quá trình chuyển đổi sang {value0} đã bị hủy.` It makes the conversion process and target explicit. Native-speaker validation is especially needed here.
- **Arabic, Spanish, Hindi, Indonesian, Japanese, Korean, Brazilian Portuguese, Simplified Chinese, Traditional Chinese — provisionally accept current.** Each current cell retains `{value0}` exactly once and appears to preserve the cancellation meaning; native-language idiom was not independently confirmed by a native speaker.

## Limits

No native-speaker approval is claimed. This is a text-only semantic review; it does not establish locale-preferred terminology or visual fit in the application. The three proposals are exact-hash review suggestions, not repository changes or accepted PR edits. The full exact-hash ledger, including per-cell rationale, placeholder counts, source metadata, line hashes, and evidence-file checksums, is in `proposal-acceptance-ledger.json`.

## Checksums

`proposal-acceptance-ledger.json` and this report are listed in `checksums.sha256` alongside their computed SHA-256 values.
