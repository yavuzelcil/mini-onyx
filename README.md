# Mini Onyx

Mini Onyx is a small educational implementation of the main architectural
ideas used by Onyx.

The current version contains a typed end-to-end chat flow:

```text
React
→ Next.js proxy
→ FastAPI
→ Pydantic
→ chat service
→ JSON response
```

## Requirements

- Git
- uv
- Python 3.13
- Bun
- Docker Desktop

Docker is not required for the current stage.

## Setup

Install the Python environment:

```powershell
uv sync
```

Install the frontend environment:

```powershell
Set-Location web
bun install --frozen-lockfile
Set-Location ..
```

## Run

Start the backend from the project root:

```powershell
uv run uvicorn mini_onyx.main:app --app-dir backend --reload --port 8000
```

Start the frontend in another terminal:

```powershell
Set-Location web
bun run dev
```

Open:

```text
http://localhost:3000
```

## Backend quality checks

```powershell
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run ty check
```

## Frontend quality checks

```powershell
bun --cwd web test
bun run --cwd web typecheck
bun run --cwd web build
```

## Project structure

```text
backend/mini_onyx/
├── chat/                  Chat service layer
├── server/query_and_chat/ HTTP router and Pydantic models
└── main.py                FastAPI application

tests/                     Backend tests
web/app/                   Next.js pages and layout
web/lib/                   Frontend API layer and tests
```
