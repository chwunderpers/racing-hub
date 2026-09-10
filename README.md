# Motorsport Hub

Local-first proof of concept for publishing a curated motorsport schedule.
The first publication contains the approved English Formula One Australian
Grand Prix fixture, persisted in PostgreSQL and projected to GraphDB before
the Meeting appears in the React schedule with its source and retrieval time.

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

GraphDB Workbench is at <http://localhost:7200>. Compose provisions the
`motorsport` repository with OWL 2 RL optimized reasoning, then runs the
one-shot bootstrap before starting the API. Service ports bind to loopback;
these development credentials and unauthenticated services are not for hosting.

GraphDB 10.8 may enable anonymous usage statistics by default depending on
the license. Disable them in Workbench under Setup > Repositories > Edit
common settings. This stack does not claim to disable telemetry automatically.

Stop the stack with `docker compose down`. Add `--volumes` to also delete the
local PostgreSQL and GraphDB data volumes.

## Publication

The checked-in fixture is an approved, fixed candidate envelope, not a live
source fetch. Its retrieval timestamp is fixture data. The browser has no write
endpoint; maintenance runs through the private command:

```powershell
docker compose run --rm bootstrap
```

The command prints a content-derived version. Repeating the same envelope
creates no duplicate canonical resources. PostgreSQL stages the version, GraphDB
writes a named graph and verifies agreement, and only then PostgreSQL atomically
promotes the schedule. A failed update leaves the previous schedule visible;
staged versions remain available for retry. PostgreSQL outages make reads
unavailable until it recovers, but do not replace the last complete version.

GraphDB is an administrative projection, not a public read API. It contains
staged and historical graphs. Query the exact promoted version, never the union
of all named graphs, when reading published data. Obtain that version with:

```powershell
docker compose exec database psql -U motorsport -d motorsport -c "SELECT current_version FROM publication_state"
```

Use the returned version in Workbench:

```sparql
PREFIX msh: <https://w3id.org/motorsport-hub/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?meeting ?name WHERE {
	GRAPH <https://w3id.org/motorsport-hub/graph/publication/VERSION> {
		?meeting a msh:Meeting ; rdfs:label ?name .
	}
}
```

This tracer supports one Meeting per publication. Multi-meeting snapshots,
source acquisition, and identity review workflows are later slices.

## Run for development

Use Python 3.12 and Node.js 24.

Start the Compose stack first to provision both stores and the fixture. Stop
the Compose frontend and backend before using their ports for local development:

```powershell
docker compose stop frontend backend
```

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

Run the real-service tests against the initialized local PoC (they republish the
fixture and leave staged test versions, so do not target a shared database):

```powershell
$env:PYTHONPATH = "backend"
$env:TEST_DATABASE_URL = "postgresql://motorsport:motorsport@127.0.0.1:5432/motorsport"
$env:TEST_GRAPHDB_URL = "http://localhost:7200"
.venv\Scripts\python -m pytest backend\tests\test_services_integration.py -q
```

Without those variables, service tests skip; unit tests do not require Docker.