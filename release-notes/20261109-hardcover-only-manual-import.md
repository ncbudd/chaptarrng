---
category: fixed
audience: users
area: imports
action: Retry manual imports with only Hardcover selected after updating.
breaking: false
---

When only Hardcover is selected in Metadata Provider settings, manual imports now look up selected author and edition IDs in Hardcover. Previously they could report an available edition missing from the author catalog unless the legacy `HARDCOVER=true` environment mode was also set.
