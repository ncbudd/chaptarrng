# ChaptarrNG PR #190 W950–W999 independent cross-review

## Pinned state and input integrity

PR #190 remained OPEN/DRAFT at head `961d3102ad3098ee188a6c87a0c88eea5f5ab332`, tree `c46078c93545042313aa1b35bc3b283b1f3b5406`. The live API head and branch ref agreed at the final requery. The exact current worktree was clean. The primary packet is `/mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-0950-0999-primary-20261102/`; its `SHA256SUMS` file SHA-256 is `29e46a5d5b9a0a806ea54504f2697635203330eded7d3ac8276b2d7a9ad40a41`, and its manifest SHA-256 is `95179dd3faa69cecee69e15acef6d0d779db41ba38605dd6897138efa672a835`. All primary-packet checksums passed.

At the exact PR head, I independently read back all 600 current cells (50 source IDs × 12 locales), verified the source queue positions, English source/catalog hashes, target catalog hashes and values, 12 catalog key sets, and all 50 provider enum caller lines. The MyAnonAMouse source context identifies every selected value as a standalone language option rendered through the provider schema/select path. Placeholder, markup, ICU, and protected-literal failures are zero for this window. The prior W949 boundary was retained from the primary packet; this cross-review does not reopen earlier positions.

## Independent dispositions

- Primary proposals: 12 reviewed; **12 accepted**, 0 revised, 0 held.
- Independent accept-current sample: all 12 locales across positions 950, 951, 954, 958, 963, 968, 969, 971, 973, 984, 986, 991, 992, 995, and 999: 170 primary keep cells.
- Sample result: 158 retain-current, 7 missed corrections, 4 refinements, and 1 hold for a native Indonesian reviewer.

| Position | Locale | Current | Independent recommendation | Result |
| --- | --- | --- | --- | --- |
| 951 | vi | Bengali | Tiếng Bangla | correction |
| 958 | de | Kroatische | Kroatisch | correction |
| 963 | vi | Farsi | Tiếng Ba Tư | correction |
| 969 | es | Gujarati | Guyaratí | correction |
| 984 | de | Malaysisch | Malaiisch | correction |
| 986 | vi | Manx | Tiếng Manx | correction |
| 995 | ja | スコットランド・ガエリック | スコットランド・ゲーリック語 | correction |
| 950 | vi | Ả Rập | Tiếng Ả Rập | refinement |
| 971 | ja | ヒンディー | ヒンディー語 | refinement |
| 991 | fr | Le portugais brésilien (BP) | Portugais brésilien (BP) | refinement |
| 992 | pt-BR | O Punjabi | Panjabi | refinement |
| 963 | id | Farsi | native-speaker decision | hold |

The German Croatian finding is supported by Duden: `Kroatisch` is the language noun, while `Kroatische` is a substantivized adjective permitted only with a definite article. Duden distinguishes `Malaiisch` (the language) from `malaysisch` (relating to Malaysia or Malaysians). RAE-DLE gives `guyaratí` as the Spanish language name. Current CLDR 49 supports `Tiếng Bangla`, `Tiếng Ba Tư`, `Tiếng Manx`, `Tiếng Ả Rập`, and Korean `말레이어`; Kotobank/Britannica gives `スコットランド・ゲーリック語`. Priberam and Infopédia give `panjabi/panjábi` as the Portuguese language noun. Sources are listed in `evidence-sources.json`.

The French and Brazilian Portuguese article changes are marked refinements because the current phrases remain intelligible but are less consistent with bare enum option labels and surrounding language-name rows. Vietnamese Arabic and Japanese Hindi are likewise refinements, not semantic failures. Indonesian Farsi remains held because source-equality alone does not establish a defect for an endonym; a fluent reviewer should choose between retaining `Farsi` and using `Bahasa Persia`.

## Limits and handoff

This is an independent machine-assisted contextual cross-review, not qualified native-speaker approval or headed-browser acceptance. The Chaptarr repo runbook and Hindsight policy require these gates to remain separate. No repository or PR files were changed, and no tests, builds, scans, CI, browser work, releases, tags, or merges were run. Root adjudication should apply accepted primary fixes and the seven missed corrections, resolve the four refinements, and keep the Indonesian Farsi cell open for qualified native-speaker review.
