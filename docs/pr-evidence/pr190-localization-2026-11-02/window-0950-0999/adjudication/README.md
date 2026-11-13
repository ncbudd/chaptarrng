# ChaptarrNG PR #190 W950–W999 third-party adjudication

## Scope and pinned inputs

This packet adjudicates the 12 primary correction proposals and the independent cross-review’s 170-row accept-current sample for 15 language-name source positions across all 12 locales. It is pinned to base/head `961d3102ad3098ee188a6c87a0c88eea5f5ab332` and tree `c46078c93545042313aa1b35bc3b283b1f3b5406`. The primary packet attests 600 cells (50 source IDs × 12 locales); the adjudication ledger has 182 findings (12 primary proposals + 170 sampled current rows).

Both input packet checksum manifests were verified before adjudication. The primary and cross-review packet locations and hashes are recorded in `input-attestation.json`. Exact source IDs, values, catalog hashes, caller-context hashes, structural checks, decisions, and evidence IDs are retained in `adjudication-ledger.jsonl`.

## Approved target changes

| Position | Locale | Source | Current | Final target | Decision |
| ---: | --- | --- | --- | --- | --- |
| 950 | vi | Arabic | Ả Rập | Tiếng Ả Rập | adopt-refinement |
| 951 | vi | Bengali | Bengali | Tiếng Bangla | adopt-missed-correction |
| 957 | de | Chinese | chinesisch | Chinesisch | accept-primary-correction |
| 958 | de | Croatian | Kroatische | Kroatisch | adopt-missed-correction |
| 963 | vi | Farsi | Farsi | Tiếng Ba Tư | adopt-missed-correction |
| 968 | es | Greek, Ancient | Griego, Antiguo | Griego antiguo | accept-primary-correction |
| 968 | fr | Greek, Ancient | Grec, ancien | Grec ancien | accept-primary-correction |
| 969 | es | Gujarati | Gujarati | Guyaratí | adopt-missed-correction |
| 971 | ja | Hindi | ヒンディー | ヒンディー語 | adopt-refinement |
| 973 | ar | Icelandic | الاسلندية | الأيسلندية | accept-primary-correction |
| 980 | de | Korean | koreanisch | Koreanisch | accept-primary-correction |
| 984 | de | Malay | Malaysisch | Malaiisch | adopt-missed-correction |
| 984 | ko | Malay | 말레이시아어 | 말레이어 | accept-primary-correction |
| 986 | es | Manx | El Manx | Manés | accept-primary-correction |
| 986 | vi | Manx | Manx | Tiếng Manx | adopt-missed-correction |
| 991 | fr | Brazilian Portuguese (BP) | Le portugais brésilien (BP) | Portugais brésilien (BP) | adopt-refinement |
| 992 | de | Punjabi | Die Punjabi | Pandschabi | accept-primary-correction |
| 992 | es | Punjabi | El Punjabi | Punyabí | accept-primary-correction |
| 992 | fr | Punjabi | Le Punjabi | Pendjabi | accept-primary-correction |
| 992 | pt-BR | Punjabi | O Punjabi | Panjabi | adopt-refinement |
| 995 | es | Scottish Gaelic | Escocés gaélico | Gaélico escocés | accept-primary-correction |
| 995 | ja | Scottish Gaelic | スコットランド・ガエリック | スコットランド・ゲーリック語 | adopt-missed-correction |
| 999 | vi | Spanish | Tây Ban Nha | Tiếng Tây Ban Nha | accept-primary-correction |

## Sample decisions and hold

- **12/12 primary proposals accepted.**
- **7 missed corrections adopted** from the accept-current sample.
- **4 refinements adopted** for bare option-label consistency and established locale display forms.
- **158 sampled current targets retained.**
- **1 Indonesian Farsi target held** unchanged pending a fluent Indonesian reviewer.

That yields **23 approved target changes** in this window. The held value remains `Farsi`; it is not counted as accepted or native-speaker approved. CLDR 49 uses `Persia` in Indonesian, while `Farsi` may also be a recognized endonym. This review does not choose a preferred product form.

The refinements are label-style improvements, not claims that every current phrase was semantically wrong. In particular, French `Le portugais brésilien (BP)` is understandable; CLDR’s bare display name is `portugais brésilien`, so the article can be removed while retaining the provider’s BP qualifier.

## Evidence and context

The primary and sample proposals were checked against the pinned caller context: every source is a standalone language option in the MyAnonaMouse provider enum/select flow. Authoritative dictionaries support the language nouns and spelling distinctions: Duden for German, RAE-ASALE DLE and FundéuRAE for Spanish, Larousse for French, and Priberam for Portuguese. Unicode CLDR 49 supports the corresponding locale display names, including Vietnamese language-marker forms, Japanese `語`, Korean Malay, Spanish Ancient Greek and Scottish Gaelic, and French Brazilian Portuguese. Kotobank/Britannica supports the Japanese Scottish Gaelic form; the Arabic Academy PDF supports the Icelandic spelling. See `evidence-sources.json` and each ledger row’s evidence IDs.

All 12 catalog files, key sets, source/target hashes, and direct provider callsites were re-attested in the input review. Placeholder, markup, ICU, and protected-literal failures are zero for this window. The sample includes 15 selected source positions in each of the 12 locales; `summary.json` records locale-by-locale coverage.

## Live PR requery

At seal, GitHub PR API heads and commit trees were requeried for all seven localization PRs. They remain unchanged from the previously attested final state; see `all-seven-pr-heads-at-seal.json`. PR #190 still has head `961d3102ad3098ee188a6c87a0c88eea5f5ab332` and tree `c46078c93545042313aa1b35bc3b283b1f3b5406`.

## Limits and handoff

This is static machine-assisted contextual adjudication, not qualified native-speaker approval or headed-browser review. The 418 primary accept-current cells outside the independent 170-row sample are outside this adjudication’s independent scope. Earlier positions are not reopened; W949 remains the boundary.

No repository or PR files were edited. No tests, builds, scans, CI, browser work, releases, tags, or merges were run.
