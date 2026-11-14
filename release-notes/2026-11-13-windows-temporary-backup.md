---
category: bug-fix
audience: operators
area: backups
action: none
breaking: false
---
Fixes temporary database backup creation on Windows by releasing the staged SQLite file before it is added to the archive.
