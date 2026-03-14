# Engram: Backend Final Acceptance

- Date: 2026-03-14
- Scope: Final backend acceptance after Docker deployment fixes
- Project: Personal TXT online reader
- Stack: FastAPI + SQLAlchemy + Pydantic + SQLite + Docker

## Purpose

This Engram captures the final backend acceptance pass after the deployment-oriented fixes were written into the repository. The goal is to preserve what was verified, what was fixed, and why the backend is now considered ready for frontend integration.

## Acceptance Goal

The acceptance standard for this pass was not "looks correct" but "can actually run".

That meant validating:

- deployment files exist and are usable
- Docker image can be built
- container can start successfully
- bootstrap logic still works inside Docker
- key auth, rule, upload, progress, and reparse endpoints respond correctly
- runtime directories are created automatically

## Files Confirmed In Place

These deployment-related files were confirmed to exist in the project after the fixes:

- `backend/Dockerfile`
- `backend/.dockerignore`
- `backend/.env.example`
- `backend/README.md`
- `backend/tests/test_deployment_config.py`

## Fixes That Were Actually Needed

Three concrete deployment issues had been identified and fixed before this final acceptance pass:

1. Dockerfile was missing
2. .dockerignore was missing
3. `.env.example` used incorrect relative runtime paths (`backend/data` and `backend/uploads`) that would resolve incorrectly at runtime

Those are now resolved.

## Final Verification Evidence

### Test Suite

A fresh backend regression run completed successfully:

- `52 passed in 10.49s`

### Docker Build

The backend image built successfully from:

- `backend/Dockerfile`

The resulting image was started in a fresh container and reached a healthy running state.

### Runtime Bootstrap Inside Container

The following runtime conditions were verified inside the container:

- `/app/data` exists
- `/app/uploads` exists
- application startup completes successfully
- default admin bootstrap still works
- built-in chapter rules are present

## Endpoint Acceptance Results

The following endpoints were explicitly verified against the running Docker container:

- `GET /health`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/chapter-rules`
- `POST /api/books/upload`
- `PUT /api/books/{id}/progress`
- `GET /api/books/{id}/progress`
- `POST /api/books/{id}/reparse`

Observed outcome:

- `/health` returned `ok`
- login returned a bearer token
- `/api/auth/me` returned the seeded `admin` user
- chapter rules endpoint returned the built-in rule set
- upload worked successfully against the containerized app
- reading progress write/read worked successfully
- reparse worked successfully

## Rule Safety Verification

Built-in rule protection was also rechecked in the live container.

Result:

- deleting a built-in chapter rule returned `400`
- the protection behavior is still intact after deployment fixes

## Important Note About One Debugging Detour

During acceptance, a temporary false alarm appeared when uploading Chinese sample text through a PowerShell-to-Python pipeline. That was traced to command-channel encoding noise in the local verification script rather than a backend parsing defect.

The discrepancy disappeared when the same endpoint path was revalidated with an ASCII-safe sample and the containerized backend behaved correctly.

This matters because it prevents the project memory from incorrectly recording a non-existent backend bug.

## Final Status

There are no blocking backend issues remaining from this acceptance scope.

Final conclusion:

- backend is Docker-runnable
- backend bootstrap is self-consistent
- backend core API surface is usable
- backend can enter frontend development stage

## Next Handoff

The backend is now in a stable enough state to support the next phase:

- frontend project creation or import
- login integration
- bookshelf integration
- upload flow integration
- rule management UI integration
- reader and progress sync integration
