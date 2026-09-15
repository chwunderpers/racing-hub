# Racing Hub

Repository: <https://github.com/chwunderpers/racing-hub>.
See [the repository rename record](docs/repository-rename.md) for preserved
GitHub history and stable data identifiers.

Local-first proof of concept for publishing a curated motorsport schedule.
The first publication contains the approved English Formula One Australian
Grand Prix fixture, persisted in PostgreSQL and projected to GraphDB before
the Meeting appears in the React schedule with its source and retrieval time.

## Run with Compose

For a reproducible complete-stack check from a clean Git checkout, use the
[isolated acceptance and recovery workflow](docs/acceptance.md). It starts a
separate licensed GraphDB service, configures least-privilege credentials and
runs all backend, frontend and desktop/mobile acceptance checks without
replacing an existing local publication.

Prerequisites: Docker with Compose v2 and a valid GraphDB license outside the
repository. Set `GRAPHDB_LICENSE_FILE` to its absolute path in the shell or an
ignored `.env` file. The license is mounted read-only; never commit its contents.

The PostgreSQL credentials in `compose.yaml` are development-only placeholders.
For the persistent stack, follow [GraphDB and assistant security setup](docs/assistant.md)
after initial bootstrap and before using the assistant. The acceptance runner
automates equivalent setup only for its disposable stack.

```powershell
docker compose up --build
```

Compose uses Microsoft's Python package feed proxy for backend image builds
because Docker Desktop may not reach PyPI's file CDN on managed networks. Set
`PIP_INDEX_URL` before running Compose to use another approved PEP 503 index.

Open <http://localhost:5173>. FastAPI is available at
<http://localhost:8000/docs> and its health endpoint is
<http://localhost:8000/api/health>.

The optional **Ask** panel answers schedule and canonical-resource questions with
source citations and an explicit display time zone. See [assistant setup and
privacy boundaries](docs/assistant.md) for the approved Azure deployment, local
API-key configuration and restricted PostgreSQL reader provisioning.

GraphDB Workbench is at <http://localhost:7200>. Compose provisions the
`motorsport` repository with OWL 2 RL optimized reasoning, then runs the
one-shot bootstrap before starting the API. Service ports bind to loopback;
these development credentials and loopback-only services are not for hosting.

GraphDB 11.5.0 is the default and the live local database. Native MCP is available
at <http://localhost:7200/mcp>; initialization, tool discovery and a bounded
publication query were verified. The assistant uses restricted native MCP with
publication-scoped queries; see [assistant security](docs/assistant.md) and
[migration results and configuration](docs/graphdb-upgrade.md).

GraphDB may enable anonymous usage statistics by default depending on
the license. Disable them in Workbench under Setup > Repositories > Edit
common settings. This stack does not claim to disable telemetry automatically.

Stop the stack with `docker compose down`. Do not add `--volumes` unless you
intend to permanently delete local data. See [backup and restore](docs/acceptance.md)
before destructive maintenance.

## Publication

The checked-in fixture is an approved, fixed candidate envelope, not a live
source fetch. Its retrieval timestamp is fixture data. The browser has no publication write
endpoint. Bootstrap initializes only an empty store and never replaces an existing
publication:

```powershell
docker compose run --rm bootstrap
```

The command prints the current content-derived version. Repeating the same envelope
creates no duplicate canonical resources. PostgreSQL stages the version, GraphDB
writes a named graph and verifies agreement, and only then PostgreSQL atomically
promotes the schedule. A failed update leaves the previous schedule visible;
staged versions remain available for retry. PostgreSQL outages make reads
unavailable until it recovers, but do not replace the last complete version.

Competition and Circuit identity keys are explicitly approved in the candidate
envelope, independent of display labels. Full envelopes, including source evidence,
are stored immutably by version. `publication_envelope(version)` provides the
maintenance read for those records. `/api/schedule` returns `publicationVersion`
with each Meeting so graph consumers can select the same snapshot.

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

For schedule changes, select **Racing Review** in VS Code Chat and provide a
structured candidate JSON file. The private agent previews one Review Item,
records the exact human decision, then asks separately for publication approval.
See [the review workflow](docs/review-workflow.md) for commands, candidate and
decision formats, audit files and failure recovery. Acceptance alone never publishes.

Select **Racing Source** to investigate official sources, fetch Formula One, GT World
Challenge Europe or NLS into private review, or replay captured 2026 facts. F1 covers 23
numbered Meetings and 115 available Sessions; GT covers ten Rounds and two unnumbered
prologues at date-level precision. GT acquisition retains timetable observations
without inventing canonical Sessions. NLS adds eight championship Meetings with
ten Rounds and seven unnumbered test Meetings, 31 known track periods, and explicit
incomplete coverage. See [the source workflow](docs/source-workflow.md) for commands,
coverage, time semantics, limitations and Chris's standing local-PoC authorization.

Season publications include Rounds, Sessions, revision/status and provenance in
PostgreSQL and the exact versioned GraphDB projection. The browser provides
identity-based Competition/Circuit/date filters, shared-Circuit detail links,
field-level GT provenance, shareable detail URLs, and browser-local,
event-local, UTC or selected IANA time displays. Unresolved dates and clocks retain
their source precision. Failed/expired source checks and newer candidates awaiting
review visibly mark the last valid schedule stale. Existing single-Meeting
publications remain compatible and are not replaced by installation or fetch.

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

Run the real-service tests using the local PoC services. The supplied PostgreSQL
login must be able to create temporary databases; GraphDB must allow repository
creation. Every test creates its own uniquely named database and repository and
removes both afterward. The demo database and `motorsport` graph are not modified:

```powershell
$env:PYTHONPATH = "backend"
$env:TEST_DATABASE_URL = "postgresql://motorsport:motorsport@127.0.0.1:5432/motorsport"
$env:TEST_GRAPHDB_URL = "http://localhost:7200"
.venv\Scripts\python -m pytest backend\tests\test_services_integration.py -q
```

Without those variables, service tests skip; unit tests do not require Docker.
Do not target production/shared services. If the process is forcibly terminated,
resources named `review_test_<uuid>` may remain; remove only those confirmed to
belong to the interrupted test run.