---
category: fixed
audience: users, operators
area: download-clients
action: Pull a Docker image containing this fix and restart ChaptarrNG before configuring remote path mappings.
breaking: false
---

Fixed remote path mappings not saving, showing an empty list, or returning default test results because a direct-download client's private no-op mapping service was selected instead of the real database-backed service. Mappings now persist and survive restarts.
