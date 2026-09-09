# Motorsport Hub

Local-first proof of concept for publishing a curated motorsport schedule. The
initial tracer provides PostgreSQL readiness, a FastAPI contract, and a React
empty-schedule experience.

## Run with Compose

Prerequisite: Docker with Compose v2.

The credentials in `compose.yaml` are development-only placeholders for this
local proof of concept.

```powershell
docker compose up --build
```

Compose uses Microsoft's Python package feed proxy for backend image builds
because Docker Desktop may not reach PyPI's file CDN on managed networks. Set
`PIP_INDEX_URL` before running Compose to use another approved PEP 503 index.

Open <http://localhost:5173>. FastAPI is available at
<http://localhost:8000/docs> and its health endpoint is
<http://localhost:8000/api/health>.

Stop the stack with `docker compose down`. Add `--volumes` to also delete the
local PostgreSQL data volume.

## Run for development

Use Python 3.12 and Node.js 24.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r backend\requirements-dev.txt
$env:PYTHONPATH = "backend"
.venv\Scripts\uvicorn app.main:app --reload
```

In a second terminal:

```powershell
Set-Location frontend
npm ci
npm run dev
```

Vite serves the app at <http://localhost:5173> and proxies `/api` requests to
the backend at port 8000.

## Verify

```powershell
$env:PYTHONPATH = "backend"
.venv\Scripts\python -m pytest backend\tests -q
.venv\Scripts\python backend\generate_openapi.py
Set-Location frontend
npm run generate-api
npm test
npm run build
```

Regenerate `frontend/src/api/schema.d.ts` whenever the backend HTTP contract
changes.