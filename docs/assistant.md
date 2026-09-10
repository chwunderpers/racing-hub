# Schedule And Documentation Assistant

Issue #8 uses Python Microsoft Agent Framework with three backend-owned tools:
`schedule`, `search_documentation`, and `lookup_iri`. PostgreSQL is the read
authority. GraphDB native MCP integration remains Issue #9; no graph query tool,
SQL execution tool, browsing tool, publication operation or maintenance command
is exposed to the model.

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

## Publication And Search

The canonical RDF builder supplies the resource IRIs and types used to generate
one English Markdown document per typed resource. Markdown includes validated
YAML front matter (`iri`, `rdfTypes`, `title`, `language`, `publicationVersion`).
Explicit non-English literals, duplicate document IRIs, unknown resource IRIs,
type/label mismatches, and broken canonical Markdown links are rejected.

These are generated documents stored as Markdown in PostgreSQL, not a crawl of
repository Markdown. Private source notes, review receipts, credentials, license
files, and maintenance instructions are never indexed. Reviewer identity and
authorization fields are omitted from the public projection. An `en` declaration
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

Retrieved text is untrusted evidence, never tool instructions. The available
capabilities enforce the read-only boundary even if the model mishandles an
injection. Citation validation proves a source was retrieved, not that every
natural-language claim is entailed by it; grounded-answer evaluation remains
necessary. Errors exposed to the browser and model are sanitized.