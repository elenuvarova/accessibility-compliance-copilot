# Accessibility Compliance Copilot

Scans a website for accessibility issues, groups them by component and severity, maps them to WCAG 2.2 AA, and builds a prioritized actionable backlog — with an honest split between what automation can verify and what needs human review. Deploys free on Render.

## Stack

- **Frontend:** React 18, Vite 5
- **Backend:** Python 3.10–3.12, FastAPI, SQLModel (SQLAlchemy) — Docker uses 3.12
- **Scan engine:** Node.js, Playwright, axe-core (spawned as a subprocess by the API)
- **Database:** SQLite locally (zero install), PostgreSQL on Render — same code, no changes
- **Deploy:** Render free tier (free web service + free Postgres), provisioned via `render.yaml`

## Project structure

```text
.
├── backend/            Python FastAPI — API, business logic, DB
│   ├── main.py
│   ├── models.py       SQLModel tables: Project, Scan, Page, Issue
│   ├── database.py     Engine from DATABASE_URL (postgres) or SQLite
│   └── requirements.txt
├── scan-worker/        Node.js — Playwright + axe-core scan script
│   ├── package.json
│   └── scanner.js      Accepts a URL via argv, outputs axe results as JSON
├── frontend/           React + Vite
│   └── src/
│       ├── App.jsx     Scan form, results table, auto/needs-review badges
│       └── styles.css
├── Dockerfile
├── render.yaml
└── .env.example
```

## Local development

No database to install — SQLite is created automatically on first run.

**One-time setup — scan worker (Node + Playwright Chromium):**

```bash
cd scan-worker
npm install
npx playwright install chromium
```

**Terminal 1 — backend:**

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

**Terminal 2 — frontend:**

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). The Vite dev server proxies `/api` to the FastAPI backend on port 8001.

## Deploy to Render

1. Push this repo to GitHub.
2. In Render, click **New → Blueprint** and connect your repo.
3. Render reads `render.yaml`, provisions the Postgres database and web service, and deploys via Docker.

> **Free tier notes:** The free web service sleeps after ~15 minutes of inactivity — expect a ~30 second cold start. Render's free Postgres instances expire after 30 days.

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/health` | Returns `{ status: "ok", db: "sqlite" or "postgres" }` |
| `POST` | `/api/projects` | Create a project `{ name, base_url }` |
| `POST` | `/api/scans` | Start a scan `{ project_id, urls: [...] }` — async, poll for result (max 25 URLs) |
| `GET` | `/api/scans/:id` | Poll scan status, issues, and components |
| `GET` | `/api/projects/:id/components` | Components for latest scan, sorted by debt score |

## Optional API protection

By default the API is **open** so local development and the public demo work with
no auth. To lock it down in production, set `APP_API_KEY` in the backend
environment. When set, all mutating and AI/cost endpoints (`POST`/`PATCH`
`/api/scans`, `/api/projects`, `/suggest-fix`, `/holistic-review`,
`/compliance-report`, `/manual-checklist`, and the issue/check `PATCH` routes)
require the key via either header:

```text
Authorization: Bearer <key>
X-API-Key: <key>
```

To make the frontend send it automatically, set `VITE_API_KEY` to the same value
at build time. Read-only export and poll endpoints stay open. The server also
applies SSRF validation on all fetched URLs, escapes scanned-page content in the
PDF report, wraps untrusted page text in the AI prompts, sets security headers
(CSP, `X-Frame-Options`, `nosniff`), and rate-limits the AI endpoints. See
`.env.example` for all options.
