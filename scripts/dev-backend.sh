#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../backend"

uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
