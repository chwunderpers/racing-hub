# Basic Vehicle Specifications

Issue #13 adds private vehicle collection, exact evidence review, public model
details and assistant retrieval. Vehicles are a separate view, never a schedule
filter. These are model descriptions, not Entered Vehicles, detailed Technical
Specifications, Balance of Performance, setup data or Competition Eligibility.

## Pending Sample

[The inventory](../examples/vehicle-inventory.json) contains Porsche 911 GT3 R
(992, model year 2026), BMW M4 GT3 EVO and Mercedes-AMG GT3 (the successor unveiled
in 2019). Its eleven assertions cover manufacturer, canonical English model
name, category and known generation or variant. Optional mechanical fields are
absent. [Source research](vehicle-source-inventory.md) records inspected official
passages, raw download hashes and applicability limits.

**The inventory is pending human review, not accepted or published knowledge.**
Source authority, identity, wording and applicability require explicit review.
The implementation proposes `VehicleModel`, `VehicleSpecificationAssertion`,
`includesVehicle` and `vehicleField` under the existing w3id ontology authority.
The canonical ontology has not been changed. Before using this for real vehicle
publication, obtain explicit scope approval for the offline
[ontology rehearsal](ontology-maintenance.md), review its exact input hashes
and outcomes, and separately authorize any canonical migration. No proposal
approval or publication authorization is implied by this implementation.

## Private Collection

With the existing operational environment configured, from the repository root:

```powershell
$env:PYTHONPATH = 'backend'
.\.venv\Scripts\python.exe -m app.vehicle_ingestion examples/vehicle-inventory.json
```

This command only creates a private review preview. It reads the current
publication and preserves all schedules, regulation profiles and vehicles not
named in the inventory. A stale baseline blocks the preview. It never accepts a
review decision or publishes. No web assistant tool can invoke it.

The strict inventory accepts 1-20 unique models, a 1 MB inventory, and up to ten
assertions per supplied field. Each assertion requires a value, applicability,
HTTPS source URL without credentials, publisher, evidence kind, English language,
anchor, retrieval timestamp and SHA-256. Required fields are manufacturer, model
name and category. Empty optional fields and eligibility properties are rejected.

Collection is limited to the configured exact official manufacturer hosts and
English Wikipedia/Wikidata hosts on standard HTTPS. Redirects and compressed
responses are rejected; each unique URL has a 20-second HTTP timeout and a 10 MB
raw-body limit. HTML, PDF and JSON are supported. The checksum covers the exact
uncompressed HTTP response body, not extracted text. A changed or empty response
blocks collection. Successful verification updates retrieval time for the preview.
The command does not retain raw source bodies or prove the semantics of HTML/PDF
content: a matching hash is byte integrity, not proof of readable English or
authority. Inspect the exact source and anchor before creating an inventory;
consent pages and unrelated content are not evidence. Dynamic pages may change
bytes without a substantive revision; inspect and update the inventory rather
than bypassing checksum verification.

## Review And Publication

Use the existing [review workflow](review-workflow.md) and CLI. Changed vehicle
assertions appear under `vehicles/<identity>` in the preview with exact
`vehicleConfirmations` tokens. After the independent vocabulary gate is resolved,
the human decision request supplies these as `vehicle_confirmations`, along with
reviewer, rationale, sources and any other required confirmations. Source kind
is reviewed classification, not automatic approval. The exact decision digest
and the later exact publication digest remain separate confirmations. Removal
of an existing vehicle is surfaced as a missing-model conflict.

Human review must verify actual English wording; an `en` tag alone proves
nothing. Wikipedia/Wikidata must be marked `secondary`. Their reviewed values are
displayed as **Secondary Evidence**, and cannot establish Competition Eligibility.
Authoritative values take precedence over secondary values. Contradicting
authoritative values remain unresolved, without selecting a winner by retrieval
date. All differing source values and applicability statements remain visible.

## Public Reads

`GET /api/vehicles` lists the current published models.
`GET /api/vehicles/{identity}` returns typed field-level provenance, or 404.
Publication RDF generates the same document projection used by API, search and
the assistant's read-only `vehicle_specification` tool. Private review rationale
and confirmation tokens do not enter those documents. Documentation search returns
an explicit `vehicleIdentity` for the retrieval tool, alongside the model IRI.
Search, lookup and vehicle retrieval share field assertions with exact citation
IDs. The eligibility-intent tool returns insufficient evidence. Whenever vehicle
evidence is retrieved, the answer service renders a bounded descriptive response
directly from the published fields instead of allowing model-written conclusions.
Thus even a misrouted model draft claiming eligibility from category evidence is
not returned. Contradicting values and Secondary Evidence remain labelled, with
each applicability statement retained. Over-budget evidence is refused, not
silently truncated. Natural-language tool selection remains model-driven, not a
general semantic proof checker. Every vehicle view explicitly states that
eligibility is not established. Governing regulatory evidence and temporal
applicability are needed for an eligibility decision.

The UI renders only supplied fields, distinguishes source authority and conflicts,
and exposes each assertion's applicability, publisher, anchor, timestamp and
checksum. Loading, no-publication, missing-model and service-error states remain
separate from schedule state. Existing schedule filters are retained on return.

## Verification

Vehicle tests use synthetic evidence and test-only decisions. Database/GraphDB
integration tests use disposable isolated stores; SDK tests mock only the external
model transport. UI tests use mock HTTP responses. None of these approvals apply
to the real sample. Run `backend/tests/test_vehicles.py` with the existing isolated
store test environment, and `npm --prefix frontend test -- src/App.test.tsx`.

Implementation verification on 2026-09-14:

- Full backend run: 278 passed; two exact tool-list expectations failed because
	they predated `vehicle_specification`. Those expectations were updated; the
	affected assistant suite then passed all eleven tests.
- After review fixes, all 32 vehicle and assistant tests passed together against
	isolated stores, including search-to-retrieval and misrouted eligibility drafts.
- Full frontend suite: 19 passed. Production build and frontend typecheck passed.
- Focused Python typecheck: zero errors in the new vehicle modules and edited
	assistant modules. Broader checks report existing diagnostics in shared
	publication, store, review, documentation and API handlers outside these edits;
	no claim of a clean repository-wide Python typecheck is made.
- Desktop (1440 px) and mobile (390 px) browser screenshots inspected with
	synthetic HTTP responses. Expanded provenance was readable without horizontal
	overflow. These checks did not publish the pending sample.
- Two-axis review against `3b744be`: no documented standards violations; one
	low-priority duplication observation in adjacent review-token loops retained
	to avoid unrelated refactoring. Both specification defects (identity discovery
	and model-intent-dependent eligibility refusal) were fixed and independently
	rechecked. Real source approval, vocabulary review and publication remain open.