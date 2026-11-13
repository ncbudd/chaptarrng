# ChaptarrNG PR #190 W150–W199 cross-adjudication

This exact-head cross-review covers 50 source keys × 12 direct locales = 600 cells at PR head `243f17465cc95fe84f16e17767db04a4a97ad040` / tree `25e7bd0f3adf871b9030081ebc7c49a28213c50f`.

The primary packet recorded 426 accepted current values, 30 proposed revisions, and 144 text-free holds. The blind packet recorded 536 keeps, 52 proposals, and 12 holds. Cross-adjudication selected 58 target changes, accepted 530 current values, and retained 12 hash-only holds.

The caller scan missed the dynamic `audibleMarketplaceOptions` map. The pinned `MetadataProvider.js` maps all 11 country keys at lines 62–72, calls `translate(translationKey)` at line 76, and passes the options to the selector at line 159. This resolves 132 previously held cells. Their current country/domain labels are accurate except `AudibleMarketplaceUk::id`, selected as `Britania Raya (.co.uk)`.

Four Simplified Chinese profile suggestions were rejected to preserve existing catalog terminology: `QualityProfile` is `质量配置` and `MetadataProfile` is `元数据配置` in `zh_CN.json`. The remaining 12 holds belong to an exact-key scan with no source caller; their source and target text remain omitted. The Hindi tag-mode help uses the exact translated dropdown labels and preserves the sidecar/failure behavior. Japanese and Korean no-upscale help use their exact checkbox labels.

The packet contains one row per cell, exact source/current hashes, caller evidence, reviewer candidates, the cross decision, a 58-row selected-change list, a live PR attestation, and a portable verifier. Candidate-free, primary, blind, and cross verifiers pass. The 58 selected changes were applied and pushed in product commit `7c5af0a3d824f7e680c775f657697aee2430d277`; exact catalog readback and 4,165-key parity pass for all 12 files. This is machine-assisted review; native-speaker approval is not claimed. No tests, builds, scans, or CI were intentionally run, and no workflow changes, merges, releases, or tags were made. The local push hook ran the repository release-readiness gates and single image-alias contract checks; both passed.

Run `python3 verify_cross_review.py` from this directory to verify row counts, hashes, placeholders, holds, and change inventory. The post-commit attestation records the live refs and clean mergeability. See `SHA256SUMS.txt` for packet file checksums.
