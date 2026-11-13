# Cross-audit summary

**Reviewed source:** ChaptarrNG PR #190, W0–W49, commit `7f5d99e24b054cf1437d135328c3dee565e6b318`, tree `d39f2fe8cf91a39653679980c0832c5ca400a114`.

## Cross-audit outcome

| Disposition | Cells |
| --- | ---: |
| Keep current | 514 |
| Select revision | 38 |
| Hold without wording | 48 |
| **Total** | **600** |

The 38 selected revisions preserve source placeholders and listed protected literals. The cell-level trail and selected wording are in `cross-ledger.jsonl` and `selected-proposals.jsonl`.

The 48 holds cover all locales for four keys without an exact frontend caller: `AddAuthorMonitorNewAudiobooksHelpText`, `AddAuthorMonitorNewEbooksHelpText`, `AddAuthorWhichAudiobooksToMonitor`, and `AddAuthorWhichEbooksToMonitor`. Eleven primary proposals on these keys were not advanced. `cross-audit-holds.jsonl` contains only IDs, hashes, caller counts, dispositions, and a hold reason; it contains no source, current, or proposed translation text.

`AddCustomFilter` in Spanish remains `Agregar filtro personalizado`. The proposed `Añadir` is a valid regional alternative; the supplied evidence does not establish a required style, so the change is not supported.

## Input review reconciliation

| Review | Accept current | Revise/correct | Hold |
| --- | ---: | ---: | ---: |
| Primary | 568 | 32 | 0 |
| Blind | 525 | 27 | 48 |
| Cross-audit | 514 | 38 | 48 |

The candidate-free-only reviewer covered source ordinals 0–24 (300 cells): 300 accept-current, with 264 high and 36 moderate confidence in that review. The cross-audit accepts 14 supported revisions in that same range based on caller context and the primary/blind evidence. This discrepancy is retained in the ledger rather than hidden.

## Integrity and limits

- All candidate-primary, blind packet, and nested blind-input checksum manifests passed before review and in the included copies.
- The exact source checkout was validated against the recorded head/tree, catalog file hashes and blobs, and caller file/line hashes. It was clean and unchanged.
- No repository, PR, CI, release, or tag was modified by this audit.
- No native-speaker approval is claimed. Confidence reflects this cross-review only; human language review remains appropriate before applying the selected text.
