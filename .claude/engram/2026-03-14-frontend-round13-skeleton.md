# Frontend Round 13 Engram

## Basic Info
- Date: 2026-03-14
- Project: local_txt_reader
- Scope: Frontend only
- Round: 13
- Status: Completed

## User Goal
Start generating the frontend foundation without modifying the backend. Build a real runnable skeleton for:
- Vue 3
- Vite
- TypeScript
- Vue Router
- Pinia
- Naive UI

Pages for this round are placeholders only:
- 登录页
- 书架页
- 书籍详情页
- 阅读页
- 规则管理页

## Constraints
- Only output frontend files
- Frontend must be able to start
- Business pages must require login
- API base wrapper must be complete
- Do not touch backend
- Prioritize runnable code over decorative work

## Key Decisions
- Created a standalone `frontend/` Vite + Vue 3 project
- Added route-level auth guard with `requiresAuth` and `guestOnly`
- Stored token in `localStorage`
- Added an auth store that restores login state on refresh by calling `/api/auth/me`
- Added shared API client with:
  - base URL handling
  - bearer token injection
  - query string support
  - JSON and `FormData` support
  - unified backend error parsing
- Built a single app layout for authenticated pages
- Kept business pages as placeholders to avoid overbuilding in this round

## Files Added
- `frontend/package.json`
- `frontend/index.html`
- `frontend/tsconfig.json`
- `frontend/tsconfig.app.json`
- `frontend/tsconfig.node.json`
- `frontend/vite.config.ts`
- `frontend/src/env.d.ts`
- `frontend/src/main.ts`
- `frontend/src/App.vue`
- `frontend/src/router/index.ts`
- `frontend/src/router/meta.d.ts`
- `frontend/src/stores/index.ts`
- `frontend/src/stores/auth.ts`
- `frontend/src/utils/token.ts`
- `frontend/src/types/api.ts`
- `frontend/src/api/client.ts`
- `frontend/src/api/auth.ts`
- `frontend/src/api/books.ts`
- `frontend/src/api/chapter-rules.ts`
- `frontend/src/layouts/AppLayout.vue`
- `frontend/src/components/PagePlaceholder.vue`
- `frontend/src/pages/LoginPage.vue`
- `frontend/src/pages/BookshelfPage.vue`
- `frontend/src/pages/BookDetailPage.vue`
- `frontend/src/pages/ReaderPage.vue`
- `frontend/src/pages/RuleManagementPage.vue`
- `frontend/src/styles/index.css`

## Verification
The frontend was checked against real startup requirements instead of only static inspection.

### Commands run
- `npm install --no-package-lock`
- `npm run build`

### Result
- Dependencies installed successfully
- TypeScript compilation passed
- Vite production build passed
- The frontend skeleton is runnable

## Important Fixes During Build
- Fixed request body typing in `src/api/client.ts` so plain object payloads work with TypeScript
- Added raw body detection so `FormData` upload calls are sent correctly
- Rewrote UTF-8 files without BOM because Vite/PostCSS failed to parse a BOM-prefixed `package.json`

## What This Round Already Supports
- App entry
- Global Naive UI setup
- Router setup
- Pinia setup
- Login page
- Authenticated app layout
- Token persistence
- Auth bootstrap on refresh
- Route guard redirect to login when unauthenticated
- Placeholder business pages
- API wrappers for auth, books, chapter rules, progress, and reparse

## What Is Intentionally Deferred
- Real bookshelf data rendering
- Book upload UI
- Book detail data loading
- Rule CRUD UI
- Rule test UI
- Reader UI and chapter content loading
- Progress auto-sync UI behavior

## Recommended Next Step
Continue with the next frontend round by replacing placeholder pages with real API-connected pages, starting with:
1. 登录态联调确认
2. 书架列表页
3. 上传书籍
4. 书籍详情与目录
