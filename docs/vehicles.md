# Basic Vehicle Specifications

Issue #13 adds private vehicle collection, exact evidence review, public model
details and assistant retrieval. Vehicles are a separate view, never a schedule
filter. These are model descriptions, not Entered Vehicles, detailed Technical
Specifications, Balance of Performance, setup data or Competition Eligibility.

## Published PoC Sample

[The inventory](../examples/vehicle-inventory.json) contains Porsche 911 GT3 R
(992, model year 2026), BMW M4 GT3 EVO and Mercedes-AMG GT3 (the successor unveiled
in 2019). Its eleven assertions cover manufacturer, canonical English model
name, category and known generation or variant. Optional mechanical fields are
absent. [Source research](vehicle-source-inventory.md) records inspected official
passages, raw download hashes and applicability limits.

**Published locally on 2026-09-14 under explicit delegated PoC authorization.**
The operator authorized GitHub Copilot to execute source, identity, English
wording, applicability, vocabulary and separate exact publication decisions
without repeated prompts. The [standing authorization](../reviews/requests/issue-13-standing-approval.json)
is scoped to this disposable local PoC, not production or future inventories.
The approval controls remain unchanged; records identify delegated execution,
not personal inspection of every assertion by the operator.

The accepted additive vocabulary declares `VehicleModel`,
`VehicleSpecificationAssertion`, `includesVehicle`, `vehicleField` and `value`,
with context-specific comments on reused evidence properties. The canonical
ontology is RDF-isomorphic to the rehearsed candidate. The private synthetic
rehearsal graphs were not published. See the closeout record below.

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

## Delegated Closeout

The preceding implementation-only verification predates this completed closeout.
The operator explicitly delegated all remaining Issue 13 PoC content and approval
operations on 2026-09-14. No assertion of 100% factual accuracy is made; the purpose
is exercising the collection, review, handoff and publication workflow with useful
disposable sample content.

- Ontology rehearsal first blocked three neutral `vehicleField` strings. The
	language-policy correction added only that machine field; tests still require
	English for values, applicability and publisher prose. All 29 ontology tests
	passed. The fresh rehearsal passed SHACL and all five OWL-RL competencies:
	class, inverse, shared-circuit, distinct-circuit-identities and graph-separation.
	Delta: 18 added triples, zero removed, zero migrated; 166 synthetic asserted
	triples and 607 separate inferred triples. Shared Circuit does not prove shared
	Layout. Exact inputs and report hashes are in the
	[delegated ontology acceptance](../reviews/requests/issue-13-ontology-acceptance.json).
- The live collector correctly refused changed BMW/AMG raw HTML hashes, including
	a retry after refreshing inspected captures. The final PoC handoff replayed
	bounded raw HTTP 200 captures through `prepare_candidate` using HTTPX's injected
	transport, without changing the collector or bypassing checksum validation.
	Actual capture times were restored before preview; replay time is not claimed
	as source verification time. Raw captures remain private under
	`ontology-reviews/issue-13-inputs/`. The
	[collection record](../reviews/requests/issue-13-collection.json) identifies the
	mode and exact source hashes. A future fresh ingestion still needs stable
	captures or a separately designed dynamic-source collection workflow.
- Review Item `52cc4f41-a2e2-4c0e-8455-1361e649becf` changed only the three vehicle
	entries, with no validation errors, conflicts or unresolved identities.
	[The decision request](../reviews/requests/issue-13-acceptance.json) supplied all
	three exact vehicle confirmation tokens. The existing CLI proposed and confirmed
	decision digest `001bf56e7ca3100314eef9f79c6dde35c228ce54e5c6e1e8e8c33cff5004c5da`.
	Decision `0c46c8bb-162a-46d8-8d69-4860fadd1cd3` records GitHub Copilot as delegated
	by Chris for the local PoC. No existing unrelated review item was resolved.
- A separate publication proposal and confirmation used digest
	`665d03c57f501cb6e024235b9bdf11540eda99f4c49eb9d790b746851813b74b`.
	[The receipt](../reviews/publications/0c46c8bb-162a-46d8-8d69-4860fadd1cd3.yaml)
	records publication `61f2c49c6232aa786352eeb667c102fb14ec0be341d263a68413d23e694da7b1`
	at `2026-09-14T12:57:32.100087+00:00`. The baseline was
	`5106927820d7b8d6a710009b5ff15b532df54314dd1ad391b0577a1638a72ae3`.
- Live SQL/API/RDF checks passed: three models, eleven fields, 50 Meetings,
	two regulation profiles, and exact versioned RDF agreement. Schedule and
	regulation payloads were compared unchanged before publication. Vehicle APIs
	return explicit `eligibilityEstablished: false` and no schedule vehicle filter.
- Actual configured assistant HTTP requests returned BMW's four descriptive fields
	and four field-level source citations (`stated`), then refused the NLS eligibility
	claim (`unsupported`, zero citations). Both used the completed version above;
	temporary sessions were deleted. No simulated provider was used in this check.
- The live published BMW details were inspected at 1440 px and 390 px, with source
	evidence expanded, readable provenance and no horizontal overflow. Earlier
	mock-only screenshots are not substituted for this live check.
- After vocabulary promotion and inventory refresh, all 21 vehicle tests passed
	against disposable SQL/GraphDB stores (74.01 seconds). Editor diagnostics were
	clear for the touched language policy, tests and documentation. Incremental
	closeout reviews found zero Standards hard violations and zero Spec defects;
	one nonblocking test-name heuristic was left unchanged. Reviewers inspected
	the supplied files and audit evidence, not an independently reconstructed Git
	diff, and did not independently rerun live checks or tests.