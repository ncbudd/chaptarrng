---
category: fixed
audience: users, operators
area: import
action: none
breaking: false
---
Audiobooks grabbed from usenet posts whose subject quotes a file name such as "Title - Part 02.mp3" are no longer treated as one part of a split release, so imported files are no longer renamed with a stray " (Part 2)" suffix.

This fix follows the split-release behavior in [upstream Chaptarr commit `2ed39e6c8c6ccdcae67707f6aaacdd821fb51e3f`](https://github.com/Chaptarr/chaptarr/commit/2ed39e6c8c6ccdcae67707f6aaacdd821fb51e3f), contributed upstream by [@snapetech](https://github.com/snapetech). ChaptarrNG independently adapted the quoted-filename correction; this does not imply direct contribution to or endorsement of ChaptarrNG.
