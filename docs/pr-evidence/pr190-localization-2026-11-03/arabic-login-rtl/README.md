# Arabic login direction fix

PR #190 head `46049fadfc1ad02775a4a096178bc08ca78407ad` adds Arabic (`ar`) to
the standalone login page's explicit right-to-left language list in
`frontend/src/login.html`.

The shared locale helper in
`frontend/src/Utilities/Localization/locale-utils.cjs` already classifies `ar`
as RTL. The login page keeps its own direction list, so Arabic was rendered
left-to-right there while the main interface used the shared locale behavior.
Adding the same locale tag to that page-specific list closes the mismatch; no
catalog strings or translation values changed.

This is a source-level review of the exact pushed commit. No test, build, or
browser review was run for this one-line fix. The isolated headed-browser pool
was unavailable during this turn, so visual acceptance remains outstanding.
