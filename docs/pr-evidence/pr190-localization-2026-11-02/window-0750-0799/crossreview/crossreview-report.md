# ChaptarrNG PR #190 W750–799 independent cross-review

## Pin and scope

The live PR is open and draft at head a58de8cd62a80babdca07a86d6b7d463b4a44773, tree 3baf8c11efe42c617a286cd37665e946303c6d2a, on codex/chaptarrng-localization-complete-20261031. GitHub PR, remote branch, and the detached pinned worktree agreed at final reattestation. The worktree is clean.

This review covers 50 source IDs and 600 target cells in 12 locales. I independently reread all 215 proposed changes and all 385 primary accept-current cells against the exact source and caller contexts. No repository/catalog edits, tests, builds, CI, browser actions, releases, tags, merges, or PR writes were made.

## Cross-review results

The primary supplied 215 proposals. I accept 206 as written and revise 9 proposals for W770 so they match the actual localized UI labels. I found 14 additional issues in cells the primary accepted as current, plus 2 lower-confidence refinements. The independent ledger disposition is:

| Disposition | Cells |
|---|---:|
| Accept current | 371 |
| Accept primary proposal | 206 |
| Revise primary proposal | 9 |
| Propose correction in primary no-op | 12 |
| Propose refinement in primary no-op | 2 |
| **Total** | **600** |

### W770: localized UI labels were treated as protected English text

BookshelfController says “Bookshelf only changes book monitoring. Use Author Editor…” These are names of two UI destinations. The exact-head sidebar uses translate('Bookshelf') and the Author tab uses translate('AuthorEditor'); both labels have locale-specific catalog values. The primary packet manually protected English Bookshelf, and most candidates left Author Editor in English or used a different label. I reclassify Bookshelf as a localized UI label for this message and revise all 12 cells to reuse the exact catalog labels.

| Locale | Bookshelf label | AuthorEditor label |
|---|---|---|
| ar | رف الكتب | محرر المؤلف |
| de | Bücherregal | Autor Editor |
| es | Estante para libros | Editor de Autor |
| fr | Bibliothèque | Éditeur de l'auteur |
| hi | पुस्तकालय | लेखक संपादक |
| id | Rak buku | Penyunting Penulis |
| ja | 本棚 | 作者エディタ |
| ko | 책장 | 저자 편집기 |
| pt-BR | Estante | Editor de autor |
| vi | Giá sách | Trình chỉnh sửa tác giả |
| zh-Hans | 书架 | 编辑作者 |
| zh-Hant | 書架 | 作者編輯器 |

Nine proposed W770 targets are revised, and three W770 accept-current cells (ar, id, vi) become corrections. The full suggested strings are in crossreview-ledger.jsonl; the pinned UI callsites and all 12 label values are in ui-label-evidence.json.

### Additional missed corrections and refinements

W780 is “Import limit must be 0 or greater” in GoodreadsDualMediaImportListSettings.ImportLimit, a software import count cap. The current values use either a goods-import term or awkward lower-bound wording in eight locales. The independent suggestions are:

| Locale | Suggested target |
|---|---|
| de | Das Importlimit muss mindestens 0 betragen. |
| fr | La limite d’importation doit être supérieure ou égale à 0. |
| hi | आयात सीमा 0 या उससे अधिक होनी चाहिए। |
| ja | インポート上限は 0 以上である必要があります。 |
| ko | 가져오기 한도는 0 이상이어야 합니다. |
| vi | Giới hạn nhập phải từ 0 trở lên. |
| zh-Hans | 导入上限必须大于或等于 0。 |
| zh-Hant | 匯入上限必須大於或等於 0。 |

The Vietnamese change is a lower-confidence terminology refinement and should be confirmed by a native speaker.

Other independent findings:

- W784 Hindi: the current “कृपया इसे परीक्षण करने से पहले…” syntax is awkward. Suggested refinement: कृपया परीक्षण करने से पहले मेटाडेटा सर्वर URL सहेजें।
- W795 Spanish: ImageUrl es necesario has awkward gender agreement. Suggested correction: Se requiere ImageUrl.
- W797 German: Einfuhr refers to importation of goods in this context. Suggested correction: Autor wurde in die Importwarteschlange aufgenommen.

These 11 W780/W784/W795/W797 cells and all 12 W770 cells are individually recorded in missed-corrections.jsonl, with rationale, confidence, and a hash for each suggested target.

### Protected literals

The primary summary reports one current protected-literal mismatch. Exact-token rechecking found two: German W752 has ZSelected where the literal enum token is Selected, and Korean W755 has HTTP(s) without the protected :// scheme. The proposed German and Korean corrections repair both. All independent final targets pass the protected-literal checks after W770’s Bookshelf label is correctly treated as translatable UI text.

## Integrity and caller evidence

- Primary packet checksums: 26 files verified. Its repository input checksum list covers and verifies 103 exact-head files.
- Recomputed all 600 English source-string hashes and all 600 current target-string hashes directly from the pinned English and locale catalogs; zero mismatches.
- All 12 locale catalogs contain 4,165 keys, with identical key sets, no duplicate JSON keys, and no missing or extra keys.
- Rechecked 50 source rows, 65 direct source caller references across 52 files, and 76 generic error-path/pipeline references across 35 files against exact file hashes, Git blob IDs, line hashes, and neighboring context. No gaps.
- Three server-registry callsite pins (ordinals 759, 761, 763) are explicitly stale in the registry; each was refreshed to its exact current production line and that current line is pinned.
- All 600 source/current/independent-target cells have matching placeholder and markup structure. Independent final protected-literal mismatches: zero.
- Independently checked the preceding W700–749 cross-review and primary packet checksums. All 600 live locale values and all 600 source strings match the independent W700 cross-review final/source values.
- W749 boundary: all 12 live locale targets still match the prior cross-review target; all 12 boundary caller refs reattest at the pinned head.
- The source queue has 1,210 entries; the selected 50 IDs exactly match positions 750–799, and the queue remains unique through position 799 with no overlap against positions 0–749.

## Remaining review gates

> 🧠 **From Hindsight memory (Localization audit and rollout across seven apps)** — The rollout requires a separate native-speaker review and headed-browser review where applicable; a machine cross-review does not establish native-speaker approval.

This terminal cross-review did not perform headed-browser review and does not claim native-speaker approval. Both remain external review gates for the end-to-end rollout. No Arabic RTL rendering claims are made.

## Evidence files

- crossreview-ledger.jsonl: one independent row for each of the 600 cells.
- missed-corrections.jsonl: 23 independent corrections/refinements with target hashes.
- ui-label-evidence.json: exact-head UI label callsites and all localized values.
- integrity-summary.json and reattest-run.json: primary/readback/caller/W700/W749 pin results.
- crossreview-verification.json: independent output consistency checks.
- live-pin-reattestation.json: final live PR, remote branch, and worktree pin.
- CROSSREVIEW-INPUT-SHA256SUMS: repo inputs, including the two added UI label callsite files.
- SHA256SUMS: checksums for this cross-review packet.
