---
category: fixed
audience: users, operators
area: import
action: none
breaking: false
---
Import no longer adds a false split-part suffix when a Usenet subject quotes one filename like `Title - Part 02.mp3`. Upstream Chaptarr [commit 2ed39e6](https://github.com/Chaptarr/chaptarr/commit/2ed39e6c8c6ccdcae67707f6aaacdd821fb51e3f) by [@snapetech](https://github.com/snapetech) contributed split-release handling upstream; ChaptarrNG independently adapted this quoted-filename fix.
