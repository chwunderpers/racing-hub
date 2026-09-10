# Private Source Workflow

Select **Racing Source** for investigation or acquisition, then **Racing Review**
for the separately confirmed decision and publication steps. Source retrieval is
not publication approval. There is no public write endpoint or background fetch job.

## Investigation

1. Read the source inventory under `docs/sources/`. For a new source or schema
   change, inspect primary-source authority, public endpoint behavior, identity,
   time precision/offsets, rights and failure handling. Record cited findings there.
2. Retain only necessary factual schedule fields in fixtures. Never execute source
   JavaScript, use page credentials, bypass access controls or infer missing times.
3. Confirm the observed scope, missing fields and unresolved decisions. A source
   with no verified schema is a research result, not a working Adapter.

Current F1 evidence: [inventory](sources/formula-one.md) and
[verified public payload](sources/formula-one-endpoint.md). The user authorized
factual PoC acquisition on 2026-09-10; that is not legal clearance for redistribution.

## Fetch Or Replay

Use the same local Python environment and connection variables as
[private review](review-workflow.md#prerequisites). Install the pinned backend
requirements as part of operator setup. Run from the repository root:

```powershell
.venv\Scripts\python -m app.source_workflow --season 2026
.venv\Scripts\python -m app.source_workflow --fixture backend/fixtures/f1-2026-source.json
```

The first command uses ordinary sequential HTTPS GETs, parses HTML/JavaScript
syntax without execution, validates a full numbered calendar, and queues a
candidate. It initializes additive database schema only. It never initializes
GraphDB, bootstraps a sample, accepts a decision or publishes. The fixture command
is deterministic replay and does not claim a new successful source verification.
Use `--reviews-dir` to keep disposable tests separate from operator records.

Completion is `pending-review` with an item ID, `unchanged` for semantically
identical published knowledge, or `failed`. HTTP/schema failures preserve the
last Publication. Missing previously published Meetings are retained as a
conflict; absence is not cancellation. Resolve these with sourced candidate
corrections through Racing Review. A fetch never silently removes old Meetings.

## Contracts And Freshness

The Adapter emits English `SeasonCandidateEnvelope` records for one Competition
and Season with explicit Meeting, Round, Session, source and circuit IDs. Existing
Australia and Albert Park identities have explicit source-key compatibility
mappings; other identities use official numeric keys, never display-label joins.
Source session states map `upcoming` to `scheduled`, retain `completed` and
`cancelled`, and reject unknown states. Meeting cancellation requires an explicit
reviewed assertion; it is not inferred from missing cards or completed sessions.

Local source timestamps retain their lexical precision, offset and source zone.
An instant exists only for a clock with an explicit valid offset and consistent
IANA rules when a zone is provided. Unknown zones and contradictory offsets stay
unresolved. Date-only values never become midnight instants. Scheduled end times
are not actual finishes. Resolution uses packaged tzdata 2026.3 on every host,
independent of the system timezone database. Each clock retains that rules version
in its hashed candidate; a missing rules version blocks processing rather than
silently recomputing an accepted assertion with different rules.

Source attempts are stored separately from publication envelopes. A new retrieval
timestamp alone does not create a semantic revision. Changes in dates, sessions,
statuses, identity or provenance evidence create a pending review. Freshness expires
24 hours after the last successful source verification; failures and pending newer
revisions mark the public schedule stale immediately. After publication, a matching
fetch clears the pending-revision marker. No successful fetch means unverified.

## Coverage

The captured revision has 23 numbered Meetings and 115 available Sessions, excluding
testing. This is current calendar coverage, not complete historical cancellation
coverage. The separately reported Saudi Arabian cancellation is not reconstructed
into this F1-only fixture. The Adapter pins the observed Meeting-key inventory and
Round order and regular/Sprint session-code sets; a changed calendar fails closed until investigation verifies the new
membership and updates that manifest and fixture. New membership changes must also
be assessed against the current published baseline and human-reviewed as a whole season. Multi-Competition
ingestion, source scheduling, historical backfill and formal OWL/SHACL are outside
this slice. Existing RDF identifiers remain stable through the Racing Hub rename.