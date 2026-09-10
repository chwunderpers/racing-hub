# Schedule, Documentation And Graph Assistant

The Python Microsoft Agent Framework assistant composes PostgreSQL tools
(`schedule`, `search_documentation`, `lookup_iri`) separately from native GraphDB
MCP tools (`graph_shared_circuits`, `graph_query`). PostgreSQL selects the accepted
Publication; graph queries are pinned to that Publication's named graph. No SQL
execution, browsing, publication or maintenance capability is exposed to the model.

## Local Configuration

The approved deployment uses the Azure Responses API at
`https://admin-4138-resource.services.ai.azure.com/openai/v1/` and deployment
`gpt-6-astra`. API-key authentication was explicitly selected. Questions and
bounded published facts may be sent to that Azure deployment; credentials and
maintenance records may not.

Set `AZURE_OPENAI_API_KEY` directly in the ignored `.env` file. Do not paste keys
into chat or commit them. Optional `AZURE_OPENAI_BASE_URL` and
`AZURE_OPENAI_DEPLOYMENT` override the approved local defaults. Missing settings
produce an unavailable assistant, not a fallback model or ambient provider.

With the local PostgreSQL and GraphDB services running and the maintenance shell
configured with `DATABASE_URL`, `GRAPHDB_URL` and `PYTHONPATH=backend`, run:

```powershell
.venv\Scripts\python -m app.assistant_setup
docker compose up --build --detach --no-deps backend frontend
```

The setup verifies the current graph, backfills its search documents without
promoting a new publication, and creates/rotates the dedicated `racing_assistant`
login. Generated local and Docker connection settings are written only to `.env`.
Restart the backend after setup rotates the login. The browser never receives
database or model credentials. Do not use `docker compose config` without output
filtering, since its expanded environment includes credentials.

The provider packages are pinned to `agent-framework-core==1.17.0` and
`agent-framework-openai==1.14.2`, the stable versions available on the configured
package mirror. Responses API tool calls and structured output are covered by an
offline HTTP-transport test and an authorized live deployment check.

### Native GraphDB Setup

GraphDB remains the separately installed, licensed 11.5.0 local dependency at
`http://localhost:7200`; Docker-internal MCP uses `http://graphdb:7200/mcp`.
The Python native MCP SDK is pinned to `mcp==1.24.0`. No REST query fallback is
used by the assistant. Administrative setup and publication writes still use the
GraphDB management and RDF APIs, independently of assistant tools.

After the existing repository has been bootstrapped, run from the repository root
with `PYTHONPATH=backend`:

```powershell
.venv\Scripts\python -m app.graph_setup
docker compose restart graphdb
docker compose up -d --no-deps --wait graphdb
docker compose up -d --build --no-deps --wait backend
```

The command is for this local `motorsport` repository. It preserves other `.env`
entries and refuses to replace an existing unmanaged account. It creates separate
`racing_admin`, `racing_maintenance` and `racing_assistant` GraphDB accounts, turns
off anonymous free access and enables authentication. A built-in administrator
that still accepts the documented default password is disabled; a customized one
is not changed. Generated credentials are stored only in ignored `.env`, never
printed. If authentication is already enabled, configured administrator credentials
are required. Use the locally stored `GRAPHDB_ADMIN_USER`/`GRAPHDB_ADMIN_PASSWORD`
for Workbench administration; never paste them into chat.

The assistant has only `ROLE_USER` and `READ_REPO_motorsport`. It cannot write or
administer users/repositories. Maintenance has repository read/write permission,
not administrator privileges. Compose sends only the relevant read/write accounts
to the backend, not the administrator account. Host-side maintenance commands
also need `GRAPHDB_MAINTENANCE_USER` and `GRAPHDB_MAINTENANCE_PASSWORD` in their
process environment; do not display expanded environment values. GraphDB tools
are not advertised without `GRAPHDB_MCP_URL`, `GRAPHDB_ASSISTANT_USER` and
`GRAPHDB_ASSISTANT_PASSWORD`.

Isolated service tests additionally use `TEST_GRAPHDB_USER` and
`TEST_GRAPHDB_PASSWORD` with repository-administration permission, alongside
`TEST_DATABASE_URL` and `TEST_GRAPHDB_URL`. Only test fixtures substitute those
credentials for disposable repository creation/deletion. Never grant these
privileges to the assistant identity.

On this Windows host, use `127.0.0.1` rather than `localhost` in service-test
connection URLs: localhost PostgreSQL reader connections stalled during validation,
while the same test and full suite passed with literal IPv4. This does not change
Docker-internal service names or the browser URL.

### Query Policy And Inference

The backend parses the entire SPARQL query and allowlists its algebra, not keywords.
SELECT, ASK, CONSTRUCT and DESCRIBE execute through native MCP `sparql_query` with
the repository fixed server-side and namespace auto-expansion disabled.

- Exactly one `FROM` must identify the accepted publication graph. Default union,
  historical/staged graphs, `FROM NAMED`, `GRAPH`, federation, updates, extension
  functions, paths and variable predicates are rejected.
- Only explicit public predicates can be read. Private evidence, translation
  authorization, reviewer and rule predicates are excluded. DESCRIBE output is
  filtered to public predicates and requires explicit canonical target IRIs.
- Input is at most 12,000 UTF-8 bytes, 100 algebra nodes and 30 combined pattern
  and template triples. SELECT/CONSTRUCT/DESCRIBE require `LIMIT 1..100`; OFFSET is
  at most 1,000. CONSTRUCT only projects triples from a conjunctive matched pattern.
- Results are bounded to 100 rows or 300 triples, 90 KB decoded result text and
  128 KB per HTTP response. Unexpected compression is rejected before expansion.
  The shared 90 KB per-turn tool budget still applies. Row-limit hits are explicit.
- GraphDB enforces a 10-second query timeout, 1,000-result ceiling and
  `throw-QueryEvaluationException-on-timeout=true`. Client operations have a
  12-second read timeout, 15-second overall deadline and at most two concurrent
  graph calls per backend worker. These bounds are required local configuration,
  not a claim that another arbitrarily configured GraphDB instance is safe.

Each turn constructs its own graph client. Each query opens and closes its native
MCP session in the tool's owning async task, including cancellation; no transport or
MCP session is shared between tabs or retained across turns. Reset cancels the active
turn. All registered server tools other than `sparql_query` remain inaccessible.

The named graph contains asserted Publication facts. Shared-Circuit matches and
CONSTRUCT projections are labelled **derived from asserted premises**, not
OWL-inferred relationships. GraphDB puts inferred triples in its global default
graph, which can combine historical or unpublished premises. The assistant does
not expose that graph or claim its contents are publication-isolated; it explains
that inferred relationships are unavailable when asked. Actual inferred-fact
retrieval would require a separately approved publication-isolated inference design.

Shared-circuit questions join canonical Circuit IRIs across the Publication, not
labels or the ten-row schedule tool. Answers include competition/resource IRIs and
actual Meeting source URLs. Matching a Circuit does not prove matching Layouts or
complete season coverage. Generic graph results resolve canonical IRIs through
published documentation for citations; an ASK alone has no resource citation and
requires a separate source lookup before supporting a natural-language answer.

## Publication And Search

The canonical RDF builder supplies the resource IRIs and types used to generate
one English Markdown document per typed resource. Markdown includes validated
YAML front matter (`iri`, `rdfTypes`, `title`, `language`, `publicationVersion`).
Explicit non-English literals, duplicate document IRIs, unknown resource IRIs,
type/label mismatches, and broken canonical Markdown links are rejected.

These are generated documents stored as Markdown in PostgreSQL, not a crawl of
repository Markdown. Private source notes, review receipts, credentials, license
files, and maintenance instructions are never indexed. Reviewer identity and
authorization fields and the envelope's maintenance `evidence` narrative are
omitted from the public projection. Schedule tools expose only allowlisted field
assertions, including their own sources, subject identities, effective times and
preference flags. An `en` declaration
does not independently prove arbitrary prose is English; publication relies on
the existing approved English-envelope boundary as well as structural validation.

`search.documents` uses `(publication_version, iri)` as its key, an English
`tsvector` and a GIN index. Documents stage atomically with operational data.
Promotion verifies exact document agreement with the deterministic projection;
failed search projection retains the previous publication and retry recovers it.
Search reads expose only completed publications. The assistant's views further
restrict access to the currently promoted publication, not staged or historical
data. No vectors or model credentials are needed for ingestion or search.

The assistant login receives only schema usage and SELECT on `assistant_public`
views. It has no ownership, elevated role or raw-envelope access. Reads use fixed
parameterized SQL, read-only transactions, a three-second statement timeout and
one-second lock timeout. Model inputs cannot select a database, role or SQL query.

## Context And Bounds

Each mounted chat gets an unpredictable session capability held only in tab
memory and request headers. It is never stored in cookies, localStorage,
sessionStorage, URLs, accounts or a database. Reload, reset and duplicated tabs
start independently. Closing chat performs best-effort deletion; periodic expiry
handles abandoned tabs. Deployment currently requires one backend worker.

- Idle expiry: 30 minutes; absolute expiry: two hours; cleanup every minute.
- At most 100 sessions, four active turns, one active turn per session and 12
  completed turns per conversation.
- Messages: 2,000 characters; answers: 6,000 characters; overall request: 60 seconds.
- Tools: at most six calls, four framework iterations, 90 KB cumulative serialized
  tool data; search inputs 200 characters, at most ten results; excerpts 6,000
  characters with explicit truncation.
- Reset cancels active model work. Provider retries are disabled and calls have
  finite timeouts. Concurrent turns and exhausted budgets fail explicitly.

The application sends bounded history explicitly, with Responses `store=false`
and no provider conversation or previous-response ID. This disables application
conversation storage; it is not a promise about Azure's independent abuse-monitoring
or service retention policies. Prompt/content tracing is not enabled.

## Answers

Every answer carries the publication version, source freshness and the named IANA
display time zone. Time conversion is deterministic and only uses resolved
instants; unresolved clocks and unknown ends remain unknown. The model must
retrieve facts again each turn, not rely on prior answers or model memory.
Citation IDs are resolved server-side against sources actually returned during
that turn. Unknown or missing citations result in an unsupported-answer response.
Source URLs and retrieval times are not generated by the model.

General Meeting citations support the programme. A status, revision or alternative
assertion carries its own citation, such as the April 18 race-control bulletin for
the abandoned NLS Qualifiers Round 4, rather than the April 15 preview.

Retrieved text is untrusted evidence, never tool instructions. The available
capabilities enforce the read-only boundary even if the model mishandles an
injection. Citation validation proves a source was retrieved, not that every
natural-language claim is entailed by it; grounded-answer evaluation remains
necessary. Errors exposed to the browser and model are sanitized.