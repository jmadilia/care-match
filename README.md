# nextjs-fastapi-template

A starter template for new projects: **Next.js + TypeScript + Tailwind CSS** frontend, **FastAPI + PostgreSQL** backend.

Use it via GitHub's **"Use this template"** button, or:

```bash
gh repo create my-new-project --template jmadilia/nextjs-fastapi-template --private --clone
```

## Stack

- **Frontend**: Next.js (App Router), TypeScript, Tailwind CSS, ESLint, pnpm
- **Backend**: FastAPI, SQLAlchemy 2.0, Alembic migrations, Pydantic Settings, uv, pytest, ruff, mypy
- **Database**: PostgreSQL (via Docker Compose for local dev)
- **CI**: GitHub Actions — lints, type-checks, builds, and tests both halves on every push/PR

## Prerequisites

- [Node.js](https://nodejs.org/) 22+ and [pnpm](https://pnpm.io/) (`corepack enable` or `npm i -g pnpm`)
- [Python](https://www.python.org/) 3.12+ and [uv](https://docs.astral.sh/uv/)
- [Docker](https://www.docker.com/) (for the local Postgres container)

## Getting started

### 1. Database

```bash
docker compose up -d
```

Starts Postgres on `localhost:5433` (user/password/db: `postgres`/`postgres`/`app`). Mapped to 5433 instead of the default 5432 to avoid clashing with any native Postgres install already running on this machine.

### 2. Backend

```bash
cd backend && cp .env.example .env && cd ..
./scripts/dev-backend.sh
```

Runs `uv sync`, applies migrations, and starts the API at `http://localhost:8000` (interactive docs at `/docs`).

### 3. Frontend

```bash
cd frontend && cp .env.example .env && cd ..
./scripts/dev-frontend.sh
```

Installs dependencies and starts the app at `http://localhost:3000`, calling the backend via `NEXT_PUBLIC_API_URL`.

## Project layout

```
.
├── frontend/           # Next.js app
│   └── src/
│       ├── app/        # App Router pages
│       └── lib/        # API client, shared utilities
├── backend/            # FastAPI app
│   ├── app/
│   │   ├── api/        # Routers
│   │   ├── core/       # Settings/config
│   │   ├── db/         # Engine, session, declarative base
│   │   ├── models/     # SQLAlchemy models
│   │   └── schemas/    # Pydantic schemas
│   ├── alembic/        # DB migrations
│   └── tests/
├── docker-compose.yml  # Local Postgres
├── scripts/            # dev-backend / dev-frontend one-shot launch scripts
└── .github/workflows/  # CI
```

## Common tasks

| Task | Command |
|---|---|
| New DB migration | `cd backend && uv run alembic revision --autogenerate -m "message"` |
| Apply migrations | `cd backend && uv run alembic upgrade head` |
| Run backend tests | `cd backend && uv run pytest` |
| Lint backend | `cd backend && uv run ruff check .` |
| Type-check backend | `cd backend && uv run mypy app` |
| Lint frontend | `cd frontend && pnpm lint` |
| Build frontend | `cd frontend && pnpm build` |

## Customizing this template

After cloning for a new project:

1. Update the `name`/`description` in `backend/pyproject.toml` and `frontend/package.json`.
2. Update `PROJECT_NAME` in `backend/.env` / `.env.example`.
3. Update the `title`/`description` metadata in `frontend/src/app/layout.tsx`.
4. Replace the `items` model/routes/schemas (`backend/app/{models,schemas}/item.py`, `backend/app/api/routes/items.py`) with your own domain — they exist to prove the stack works end to end.
5. Update this README.
