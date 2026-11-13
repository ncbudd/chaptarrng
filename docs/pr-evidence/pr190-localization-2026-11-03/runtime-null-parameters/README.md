# ChaptarrNG no-parameter server message fallback correction

This static code-review follow-up is based on PR #190 parent commit 257ee0bfd45f0b8e4e280d663f4a09264697a989, tree 2f4d6eeadb8c0bf34e4dd99d12a9e341d855ea38.

## Finding

The independent read-only source review found that translateServerMessageById rejected a null parameter object and returned null. In releaseActions, absent response parameters are normalized with messageParameters || null. InteractiveSearchRow then falls back to the raw server message when the translated result is null.

This affected the valid no-parameter descriptor server.message.me59dec254c7d, “The matching torrent is no longer available in the selected download client. Search again before grabbing it.” Its caller path supplies null despite the descriptor requiring no values.

## Correction

The translator now treats null as an empty object only for descriptors that declare no parameters. Unknown IDs, arrays, primitives, and null values for parameterized descriptors retain the existing fallback behavior. The existing source ID and translated-message formatting path remain unchanged.

## Review record

- P2 caller gap found in frontend/src/Utilities/String/translateServerMessage.js:43.
- Null normalization originates in frontend/src/Store/Actions/releaseActions.js:425.
- Raw-English fallback occurs in frontend/src/InteractiveSearch/InteractiveSearchRow.js:305–312.
- The correction is limited to the translator and this evidence directory; no locale catalog or workflow file changed.
- Static diff inspection and git whitespace validation passed. No tests, builds, scans, or CI jobs were run.
