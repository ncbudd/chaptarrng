---
category: fixed
audience: operators
area: security
action: none
breaking: false
---
Containers now use .NET 10.0.15 and build bubblewrap, LAME, and FFmpeg from checksum-pinned sources; MP3 encoding stays available through a replaceable LGPL library. Runtime wget is removed. FreeBSD archives use matching .NET 10.0.15 packs, and updater signature checks use a current GitHub CLI with patched Go dependencies.
