# TXT Reader

TXT Reader is a personal TXT web reader for uploading local TXT files, parsing chapters, managing a bookshelf, configuring chapter regex rules, and syncing reading progress across devices.

## Project Overview

The project is intentionally lightweight:

- upload TXT files and keep them on local disk
- parse chapters with built-in or custom regex rules
- browse books in a bookshelf and open book details
- read chapter by chapter instead of returning the full book at once
- sync reading progress by chapter index and character offset
- support both desktop and mobile browsers

## Tech Stack

- Frontend: Vue 3, Vite, TypeScript, Vue Router, Pinia, Naive UI
- Backend: FastAPI, SQLAlchemy, Pydantic, SQLite, Python 3.11+
- Delivery: Docker and docker-compose

## Directory Structure

```text
.
|- backend/
|  |- app/
|  |- data/
|  |- uploads/
|  |- Dockerfile
|  |- README.md
|  \- requirements.txt
|- frontend/
|  |- src/
|  |- Dockerfile
|  |- nginx.conf
|  |- package.json
|  \- README.md
|- docs/
|- docker-compose.yml
|- .env.example
\- .gitignore
```

## Local Development

### 1. Start the backend

Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

macOS / Linux:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start the frontend

```powershell
cd frontend
npm install
$env:VITE_API_BASE_URL = 'http://127.0.0.1:8000'
npm run dev
```

If the backend is still running on the default address, `VITE_API_BASE_URL` can be omitted.

### 3. Local URLs

- Frontend: [http://localhost:5173](http://localhost:5173)
- Backend API: [http://localhost:8000](http://localhost:8000)
- Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

## Docker Startup

### 1. Prepare root environment variables

```powershell
Copy-Item .env.example .env
```

If you change host ports, update `BACKEND_PORT`, `FRONTEND_PORT`, and `VITE_API_BASE_URL` together so the browser and built frontend point to the same backend address.

### 2. Build and start all services

```bash
docker compose up --build
```

### 3. Docker URLs

- Frontend: [http://localhost:5173](http://localhost:5173)
- Backend API: [http://localhost:8000](http://localhost:8000)
- Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 4. Persistent data

The compose file mounts two named volumes for the backend:

- `backend_data` for the SQLite database
- `backend_uploads` for uploaded TXT files

Removing containers will not remove these volumes unless you delete them explicitly.

## Default Credentials

On first startup, the backend bootstraps a default admin account:

- Username: `admin`
- Password: `admin123`

You can override the defaults through `backend/.env` for local backend development or through the root `.env` when using Docker.

## Chapter Rule Features

- Built-in chapter rules are seeded automatically on first startup.
- Users can create, edit, test, and delete custom regex rules.
- A rule can be marked as the default parsing rule.
- Rules can be tested against uploaded books or raw text snippets before applying them.

## Reparse Behavior

- After changing a rule, you can reparse a specific book from the book detail page or the rule management page.
- Reparse refreshes the chapter list, total chapter count, and the active chapter rule for that book.
- The original TXT file is not modified during reparse.
- If no chapter matches are found, the backend falls back to a single full-text chapter so the book remains readable.

## Reading Progress Sync

- Reading progress is synced primarily by `chapter_index + char_offset`.
- `percent` is stored for UI display and progress indicators.
- The reader saves progress on chapter switches, during reading, and before page unload.
- Reading preferences such as font size, line height, and theme stay in browser `localStorage`.

## Extra Notes

- Backend local env template: [backend/.env.example](./backend/.env.example)
- Frontend standalone startup notes: [frontend/README.md](./frontend/README.md)
- Round-by-round delivery plan: [docs/IMPLEMENTATION_STEPS.md](./docs/IMPLEMENTATION_STEPS.md)
