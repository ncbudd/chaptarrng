---
category: fixed
audience: operators
area: security
action: Update Cloudron candidates when a new verified package is available.
breaking: false
---

The Cloudron proxy now forwards only WebSocket upgrade requests, preventing arbitrary client upgrade values from reaching the app. Ambiguous edition lookups no longer write user-supplied provider IDs to logs.
