---
category: fixed
audience: operators
area: security
action: none
breaking: false
---
Updated .NET 10.0.15 and container inputs. Images build bubblewrap 0.13.1, LAME 4.0, and FFmpeg 9.0.2 from checksum-verified sources, preserve MP3 encoding through a replaceable LGPL shared library, verify pinned m4b-tool, and remove runtime wget. The updater-signature verifier now uses GitHub CLI 2.104.0 and current Go `x/net` and `x/crypto` dependencies. FreeBSD archives use matching .NET 10.0.15 runtime packs from the pinned source tree.
