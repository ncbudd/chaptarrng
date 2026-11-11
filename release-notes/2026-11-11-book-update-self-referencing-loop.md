---
category: fixed
audience: users, operators
area: api
action: none
breaking: false
---
Saving a book through the API (PUT /api/v1/book/{id}) no longer fails with a 500 "Self referencing loop detected" error for books that have editions. This had caused apps that update a book right after adding it, such as SeerrNG, to mark new book requests as failed.
