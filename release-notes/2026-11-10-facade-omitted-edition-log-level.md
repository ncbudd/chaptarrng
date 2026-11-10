---
category: fixed
audience: operators
area: logging
action: none
breaking: false
---
The "Omitted edition row(s) without identity" message from the Readarr-compatible API is now a debug message instead of a warning. It was logged on every edition response and made up nearly all warning-level log output, pushing real warnings out of the rotated log files.
