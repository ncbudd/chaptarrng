---
category: fixed
audience: users, operators
area: metadata
action: none
breaking: false
---
ISBN and title lookups no longer fail with "Invalid response received from Goodreads" when the metadata server has no search. With a Hardcover token configured, they search Hardcover instead, so SeerrNG requests for books found by ISBN or title reach ChaptarrNG again.
