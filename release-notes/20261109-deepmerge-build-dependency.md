---
category: fixed
audience: operators
area: security
action: none
breaking: false
---

Build-time dependencies now use a locally hardened `deepmerge` package until an upstream patched version is available. The patch rejects prototype-modifying object keys while preserving ordinary merges.
