---
category: fixed
audience: users, operators
area: migration
action: none
breaking: false
---
BookshelfNG backup restore now rejects a saved SSL certificate path that is unavailable on the target before staging the archive. If a different startup error occurs after a restore, ChaptarrNG rolls back the database and configuration and starts once with the previous data; the failed restore and its error remain available for diagnosis.
