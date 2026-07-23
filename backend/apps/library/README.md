# Enterprise Library Management System (ELMS) Documentation

This document describes the library directories, catalog structures, borrowing rules, and circulation checking of the **library** app.

---

## 1. Bibliographic Catalog Schema
- **Book**: Master OPAC bibliographical records listing authors, publisher, category, and ISBN.
- **BookCopy**: Individual copies with barcode IDs for circulation checks.

---

## 2. Circulation Checkouts
- **BookIssue**: Tracks date issued, due date, return date, and calculated overdue fines.
- **BookReservation**: Hold queue manager.

---

## 3. REST APIs
Endpoints are mapped under `/library/api/v1/`:
- `GET/POST /library/books/`: Manage books.
- `GET/POST /library/issues/`: Checkouts list.
- `GET/POST /library/digital/`: eBooks catalog.
