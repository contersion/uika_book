# Engram: TXT Reader Backend MVP Memory

- Date: 2026-03-14
- Scope: Backend rounds 1-12
- Project: Personal TXT online reader
- Stack: FastAPI + SQLAlchemy + Pydantic + SQLite

## Purpose

This Engram captures the current backend baseline we aligned on while iterating through the MVP. The main goal is to preserve decisions, finished capabilities, cleanup status, and the next logical handoff point.

## Product Constraints We Kept

- Personal-use project first, but code structure stays clean.
- Backend and frontend are separated, but we avoid over-engineering.
- Local disk stores uploaded TXT files.
- SQLite stores structured data.
- User model and authentication stay in place even though the product is single-user oriented.
- Stability and real runnability are more important than fancy architecture.

## Backend Capabilities Completed

### Foundation

- FastAPI application bootstraps from `app.main:app`.
- CORS is configured for local frontend development.
- SQLite engine, SQLAlchemy base, session handling, and startup initialization are in place.
- Runtime directories are created automatically.
- Default admin user is seeded on first startup.
- Built-in chapter rules are seeded on first startup.

### Data Model

The backend now includes these core tables:

- `users`
- `books`
- `book_chapters`
- `reading_progress`
- `chapter_rules`

Relations are already wired for future expansion.

### Authentication

Implemented endpoints:

- `POST /api/auth/login`
- `GET /api/auth/me`

Behavior:

- password hash + verify logic exists
- signed token auth is used
- auth dependency can protect later APIs
- default user is `admin / admin123`

### Chapter Rules

Implemented endpoints:

- `GET /api/chapter-rules`
- `POST /api/chapter-rules`
- `PUT /api/chapter-rules/{rule_id}`
- `DELETE /api/chapter-rules/{rule_id}`
- `POST /api/chapter-rules/test`

Built-in rules included:

- Chinese chapter pattern
- English chapter pattern
- mixed volume/chapter pattern
- full-text single-chapter mode

Important constraints:

- built-in rules cannot be deleted
- built-in rules cannot be edited like normal custom rules
- built-in rules and current user custom rules are returned together
- only one default rule is kept active for the user scope

### Book Upload and Parsing

Implemented endpoint:

- `POST /api/books/upload`

Behavior:

- only `.txt` upload is accepted
- source file is saved locally
- encoding detection supports UTF-8, GBK, UTF-16
- file content is normalized to UTF-8 for storage/use
- book title is inferred from content when possible
- specified `chapter_rule_id` is supported
- if no rule is passed, default rule is used
- chapter parsing runs automatically after upload
- chapter records are written into `book_chapters`
- `books.total_words` and `books.total_chapters` are updated
- if no chapter match is found, parsing degrades to a single `全文` chapter instead of failing

### Books and Reading APIs

Implemented endpoints:

- `GET /api/books`
- `GET /api/books/{book_id}`
- `DELETE /api/books/{book_id}`
- `GET /api/books/{book_id}/chapters`
- `GET /api/books/{book_id}/chapters/{chapter_index}`
- `POST /api/books/{book_id}/reparse`
- `GET /api/books/{book_id}/progress`
- `PUT /api/books/{book_id}/progress`

Behavior:

- bookshelf listing supports title search
- bookshelf exposes total chapters, total words, recent read time, and progress percent
- chapter content API returns only the requested chapter body, never the full book
- deleting a book removes both database records and local files
- reparsing removes old chapters, applies the selected rule again, and persists the new TOC
- reading progress sync is last-write-wins based on `updated_at`

## Core Parsing Decision

The parsing design intentionally separates responsibilities:

- regex utilities compile and validate rules
- text splitting produces chapter segments only
- database persistence for chapters is handled separately

This keeps chapter recognition, splitting, and persistence independently replaceable later.

## Round 12 Cleanup Decisions

This last backend cleanup round focused on operational polish rather than new business features.

### 1. Global exception handling

We added application-level exception handlers for:

- HTTP errors
- validation errors
- unexpected server errors

### 2. Unified error format

Errors now return a stable envelope:

```json
{
  "success": false,
  "detail": "Request validation failed",
  "error": {
    "code": "validation_error",
    "message": "Request validation failed",
    "details": []
  }
}
```

This preserves backward-friendly `detail` access while making frontend error handling much more consistent.

### 3. Startup and seeding cleanup

Initialization flow is now easier to read:

- ensure runtime directories
- create schema
- verify DB connection
- run seeders in a controlled session

### 4. Environment and docs cleanup

Added or improved:

- `backend/.env.example`
- `backend/README.md`
- `backend/requirements.txt`

This makes first-run setup clearer and reduces hidden dependency risk.

## Verification Snapshot

Fresh verification completed after the cleanup changes.

Targeted error-handling tests:

- `2 passed`

Full backend test suite:

- `49 passed in 10.46s`

## Current Backend Status

The backend is now at a solid MVP state for moving into frontend work. The important backend contract surface is present, chapter parsing and reparsing exist, progress sync exists, and operational concerns like startup seeding and unified errors are already cleaned up.

## Likely Next Step

The next natural phase is frontend implementation against the current backend API surface:

- login state handling
- bookshelf page
- book detail page
- TOC page
- reader page
- chapter rule management UI
- upload flow
- reading progress sync wiring
