# Issue 12 Verification

Date: 2026-09-11. Scope: Formula One versus NLS, 2026 race-points allocation,
with F1 as the reference. Review baseline: `4f87d77`. Implementation is local on
`main`; no push, merge, new evidence approval or live publication is authorized.

## Delivered

- Official FIA/F1 and VLN/DMSB/NLS document authority and exact HTTPS host scopes.
  Unknown issue dates remain null, separate from approval and version dates.
- [Pending NLS inventory](../backend/fixtures/nls-2026-regulations.json): A1 and
  Bulletin 03, verified PDF hashes, 14 anchored English passages and Provisions,
  complete class-winner rows for 4h/6h formats, classification and duration
  conditions, Speed Trophy distinction, exceptions and unresolved evidence.
- Seven profile topics: scoring conditionally known; six unknown. Synthetic
  integration tests separately exercise evidenced not-published and
  not-applicable states without relabelling unknown evidence.
- Existing private ingestion/review/publication path preserves F1 and schedules,
  requires translation acceptance and publishes version-matched SQL/search/RDF.
  Incoming and outgoing amendment links remain visible in profile retrieval.
- Typed `compare_regulations` tool through the actual Agent Framework Responses
  boundary. Both Competitions use the same requested season/topic and Publication;
  optional dates annotate each Provision without inventing historical scope.
- Insufficient evidence and unresolved amendments cause explicit scoped refusals.
  The service rejects one-sided/invented citations after comparison and classifies
  supported comparisons as derived. Private reviewer/authorization metadata stays
  outside assistant retrieval and provider payloads.

## Verification

- Full backend suite with disposable PostgreSQL and GraphDB stores: **242 passed,
  zero skipped**, 814.65 seconds. Existing dependency warnings remain (703).
- Initial comparison test file: 25 cases, included in that full run. Covers private
  translation gates, authority/host/season policy, profile absence states,
  ingestion preservation, exact graph agreement, amendment traversal, temporal
  gaps, independent conflicts, scoped citations, wrong seasons and SDK refusals.
- Red/green SDK tests demonstrated and fixed acceptance of one-sided and
  date-unsupported drafts, plus generic refusals hiding the actual evidence gap.
- Focused Pyright over the changed regulation, projection, assistant/provider and
  comparison test modules: zero errors. Existing assistant regressions: 11 passed.
- Frontend: **14 passed**; `npm --prefix frontend run build` passed TypeScript and
  Vite. No HTTP schema or frontend source change was required.
- Both real NLS PDFs passed `prepare_candidate` checksum acquisition into an
  in-memory baseline, retaining F1 and schedule. No operational queue or live
  store was touched. Real pending inventory review passes schema/preview and
  remains blocked at translation acceptance before publication.
- Modified agent/skill YAML frontmatter parses; existing workflow limits remain.

## Remaining Human Gates

All 14 real Translation Records remain pending, with no reviewer or authorization.
Human review must resolve or explicitly retain the German/English approval-date
conflict, unknown issue/effective dates, incorporated DMSB details, incomplete
amendment coverage and evidence reuse conditions. No event award is established.
See [source evidence and limits](nls-regulations-source-inventory.md) and
[the private workflow](regulation-workflow.md).

The SDK evaluation uses deterministic mock model responses, not a new live Azure
evaluation. It verifies actual tool serialization, retrieval, citation ownership,
refusal guards and isolation; it does not prove arbitrary model prose semantically
correct or complete. No automatic conflict-precedence engine is claimed.

## Code Review

Baseline `4f87d77`; initial implementation commit `52f796b`. The Standards review
found no confirmed hard violations and two low-severity heuristics: loosely typed
comparison results and case-heavy SDK test setup. These remain maintainability
advisories, not demonstrated failures.

The initial Spec review identified two confirmed defects, repaired with red/green tests:
future, related amendments incorrectly blocked a currently governing historical
rule; native graph policy omitted public regulation predicates. Retrieval now
marks directly governing Provisions, discloses out-of-period related amendments
without letting them block the current rule, and permits existing public
regulation predicates through the same version/size/private-field query policy.
Post-review verification: **89 affected tests passed** (regulations, comparison,
assistant and graph queries), including 27 comparison cases and real isolated
native MCP. Pyright over all seven changed implementation modules and the
comparison suite is clean. The full suite was run once before review, as agreed;
these focused checks cover the subsequent fixes.

A follow-up Spec review found that a dated answer could cite only a future related
amendment for one Competition. The service now requires an in-scope governing
citation per side, while allowing related citations as additional disclosures.
The SDK regression went red then green; all **8 SDK comparison cases passed**
afterward, and the touched modules typecheck cleanly. Narrow review confirmed this
defect resolved. The comparison test file now contains 28 cases.

The review also identified a model-trust limitation: comparison-specific service
guards apply when the model invokes `compare_regulations`. A model that ignores
instructions and chooses only single-Competition or general retrieval tools can
still produce semantically unsupported comparison prose with valid citation IDs.
Tool choice and prose interpretation remain model-evaluated, not deterministic
intent recognition. This is an explicit residual risk, not a claim of complete
prevention. **The Spec reviewer retains this as an open P1 blocker to the strict
refusal acceptance criterion**, not a resolved finding. The implementation does
not introduce keyword-based request routing or pretend citation membership proves
what the prose says.

An explicit structured comparison mode with server-controlled retrieval was
proposed, which would extend the assistant API/UI. No routing choice was supplied;
user unavailability is not approval to expand that contract. The decision remains
pending. Complete Standards coverage found zero hard violations and two low
advisories; Spec has three repaired defects and this one unresolved blocker.

Issue #12 remains open and is not ready for full acceptance. It needs the routing
decision, real evidence review and separate exact publication confirmation. Local
implementation commits do not establish acceptance of all issue criteria.