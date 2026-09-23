# Care Match

A therapist-client matching and waitlist optimization engine: an original take on the hardest problem underneath any telehealth marketplace, which is pairing a client with the right available provider, fast, without a licensure, insurance-panel, or capacity constraint silently producing a bad match.

## Why this exists

Telehealth marketplaces all sit on top of the same hard problem: providers are a constrained, unevenly distributed resource (licensed only in certain states, paneled with only certain insurers, with a hard weekly capacity), and clients arrive with a mix of hard constraints (insurance, state, timezone) and soft preferences (specialty, modality, language, cultural fit). Naive filter-and-pick-first matching ignores marketplace-level effects: some providers get overloaded while others sit idle, and clients wait longer than they need to.

This project treats matching as a two-sided marketplace optimization problem rather than a lookup query. It builds a synthetic provider/client marketplace and compares several matching strategies, including rule-based filtering, greedy ranked assignment, and a stable-matching/optimization-based approach, against simulated demand, evaluating them on time-to-first-appointment, fill rate, and provider utilization balance.

This is a portfolio project built on synthetic data. It isn't modeled on, or affiliated with, any specific company's internal systems.

## Status

- [ ] Synthetic provider/client data generator (state, insurance panel, specialty, capacity, preferences)
- [ ] Matching engine v1: hard-constraint filtering + weighted scoring
- [ ] Waitlist optimization: priority queue with aging + urgency escalation
- [ ] Batch stable-matching pass (Gale-Shapley-style) vs. greedy assignment comparison
- [ ] Marketplace simulation + evaluation metrics (time-to-match, fill rate, utilization variance)
- [ ] Client intake + admin/ops dashboards (Next.js)

## Domain model

Entities as they land, each with a SQLAlchemy model, Alembic migration, Pydantic schema, and CRUD routes:

- [x] `Provider` (`/api/v1/providers`): license states, specialties, modalities, languages, insurance panels, weekly capacity
- [x] `Client` (`/api/v1/clients`): state, insurance payer, needed specialties, preferred modality/language, urgency
- [x] `WaitlistEntry` (`/api/v1/waitlist-entries`): tracks a client's wait, used to measure time-to-match
- [x] `Match` (`/api/v1/matches`): a client/provider pairing, tagged with the strategy that produced it
- [x] `SimulationRun` (`/api/v1/simulation-runs`): groups one experiment (seed and population size) so different strategies can be compared against the same synthetic population; clients and providers link to a run via `simulation_run_id`

## Stack

- **Frontend**: Next.js (App Router), TypeScript, Tailwind CSS, ESLint, pnpm
- **Backend**: FastAPI, SQLAlchemy 2.0, Alembic migrations, Pydantic Settings, uv, pytest, ruff, mypy
- **Database**: PostgreSQL (via Docker Compose for local dev)
- **CI**: GitHub Actions, lints, type-checks, builds, and tests both halves on every push/PR

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
