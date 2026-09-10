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
.venv\Scripts\python -m app.source_workflow --source-family gt-world-challenge-europe --season 2026
.venv\Scripts\python -m app.source_workflow --source-family gt-world-challenge-europe --fixture backend/fixtures/gtwce-2026-source.json
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
Checks are isolated by source family in `source_checks`; initialization copies legacy
F1 attempts without deleting them. The schedule is stale when any included or checked
source is stale. A GT success cannot clear an F1 failure. API freshness includes
per-source details. The current 24-hour policy is applied independently to both families.

## Coverage

The captured revision has 23 numbered Meetings and 115 available Sessions, excluding
testing. This is current calendar coverage, not complete historical cancellation
coverage. The separately reported Saudi Arabian cancellation is not reconstructed
into this F1-only fixture. The Adapter pins the observed Meeting-key inventory and
Round order and regular/Sprint session-code sets; a changed calendar fails closed until investigation verifies the new
membership and updates that manifest and fixture. New membership changes must also
be assessed against the current published baseline and human-reviewed as a whole season.
Source scheduling, historical backfill and formal OWL/SHACL remain outside this slice.
Existing RDF identifiers remain stable through the Racing Hub rename.

## GT World Challenge Europe

The [verified source inventory](sources/gt-world-challenge-europe.md) covers 12
Meetings: ten championship Rounds and two unnumbered prologues. The Adapter uses
calendar classification, not conflicting JSON-LD Round descriptions. It parses
bounded public HTML and JSON-LD without script execution. Unknown inventory,
classification or schema, missing Meetings, redirects and access controls stop acquisition.
Missing timetable tables/rows also stop acquisition. A decrease in previously
published timetable observation counts blocks review until the evidence is retained
or a corrected candidate supplies the missing observations.

Coverage is **Meeting dates**, not canonical GT Sessions. All 104 observed timetable
rows remain field-level source observations, including five unnamed Barcelona rows,
non-driving entries and dates outside Meeting bounds. No Session identity, duration,
timezone or UTC-date rollover is fabricated. The fixture is a minimal factual
date-level regression sample; live acquisition additionally retains address, operator,
cup and timetable evidence. Fixture replay therefore is not a lossless live refresh.

The versioned `gtwce-circuits-2026-v1` crosswalk uses explicit source Meeting keys.
Monza, Spa, Barcelona and Zandvoort reuse existing F1 Circuit identities. Other
Circuits have separate GT identities; Nurburgring layout remains unresolved and
must not be merged with a future NLS course by name. Every new GT Meeting requires
an explicit `source_identity/circuit_identity` resolution in the human decision.
Raw provider labels and competing classifications remain `field_assertions` with
source URL, retrieval time, locator, preference and transformation rule. Acceptance
of the candidate selects these rules; it never erases the retained alternatives.

`PublicationSnapshot` contains separately validated Competition/Season envelopes.
Fetching one season retains other published seasons unchanged. Review rejects
missing previously published Meetings or Sessions. Publication promotes all seasons
under one hash only after exact GraphDB agreement. Existing F1 candidate serialization,
publication hashes and persisted IRIs remain unchanged. Canonical IDs in schedule
responses are derived from the accepted envelope, never display-label joins.

The browser filters Circuits by `circuitId`, shows prologues without Round numbers,
and links Meetings across Competitions at a shared Circuit. Source assertions are
expandable in GT detail views. Query the exact schedule `publicationVersion`:

```sparql
PREFIX msh: <https://w3id.org/motorsport-hub/ontology/>
SELECT DISTINCT ?circuit WHERE {
   GRAPH <https://w3id.org/motorsport-hub/graph/publication/VERSION> {
      ?f1 a msh:Meeting ;
         msh:competition <https://w3id.org/motorsport-hub/resource/competition/formula-one> ;
         msh:circuit ?circuit .
      ?gt a msh:Meeting ;
         msh:competition <https://w3id.org/motorsport-hub/resource/competition/gt-world-challenge-europe> ;
         msh:circuit ?circuit .
   }
}
```

The source command queues a combined candidate, not a decision. Separate exact human
decision and publication confirmations remain mandatory. Do not mark Issue 6's
approved-season publication criterion complete until its publication receipt exists.