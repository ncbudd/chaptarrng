# ChaptarrNG PR #190 localization review and application — W400–W449

This milestone reviews 50 Core source keys across 12 locales (600 populated cells) at PR head `8ce0caa5c8c456ba5b1bcfeb0352955c93f181e7` / tree `018e46cd14424204a01be46e13e5b50f9f26ce07`. Candidate-free input, primary review, independent blind review, independent semantic cross-review, second opinion, and root adjudication are preserved in their own directories with nested checksums.

The primary review retained 513 current cells, proposed 75 changes, and held 12 callerless cells. The blind review retained 512, proposed 76 changes, and held the same 12 cells. Cross-review retained 448 values, recommended 123 corrections and 17 refinements, and kept the 12 callerless `CatalogNumber` cells as text-free hash-only holds. A separate second opinion reviewed all 140 recommendations: 134 were accepted and six adjusted. Root accepted those results after caller-context and token checks.

The exact-hash application changed 140 values across all 12 locale catalogs in product commit `3efb8f4ec37de7a9e9a7664623b1dc5fbe6f2526` (tree recorded in `application/application-readback-summary.json`). The committed-tree readback matches every selected target; all catalogs retain 4,165 keys and their original order, non-target values are unchanged, and no callerless cell changed. `application/verify_application.py` verifies this against the pinned review head.

Machine-assisted semantic review is complete for these 600 cells. Native-speaker review remains outstanding; no native-speaker approval is claimed. No exact-head product deployment exists, so this packet does not claim product-browser acceptance. The isolated Agent GUI VM was used for PR-page review only.

No workflow file changed. No hosted CI, build, scan, deployment, merge, release, or tag was run or created. One local Git pre-push hook ran `packaging/scripts/test-publish-image-aliases.sh` once during the product push on `kspld0`; it reported “ChaptarrNG and BookshelfNG retirement release-readiness gates passed” and “Single standard image alias contract tests passed.” The evidence push suppresses local hooks to avoid rerunning that script.
