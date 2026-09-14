# Issue 12 Verification

Updated: 2026-09-14. Scope: Formula One versus NLS, 2026 race-points allocation,
with F1 as the reference. Review baseline: `4f87d77`. Implementation is local on
`main`; no push or merge is authorized. The separately authorized 2026-09-14
publication and subsequent live fix below supersede the earlier pending gates.

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

The initial routing decision was pending. On 2026-09-12 the user authorized the
proposed explicit mode. The implementation below supersedes that implementation
blocker for the controlled comparison workflow, not for arbitrary chat prose.

## Explicit Comparison Mode

The Ask panel now offers Chat and Compare rules. Compare rules selects a season,
topic and optional date for Formula One versus NLS; it sends a typed `comparison`
field through the existing messages API. The server generates the scoped question,
ignores free-text scope overrides and prior chat history, and retrieves both
profiles before calling the model. Missing or unresolved evidence produces a
server refusal without a model call. Otherwise, the actual Agent Framework
provider receives only that evidence and no alternate tools. Existing in-scope
governing-citation checks apply to its answer.

This fixes optional tool routing for explicit mode. Chat remains free-form and
does not claim the same guarantee. Neither mode guarantees arbitrary generated
prose is semantically complete or correct merely because citation IDs are valid.

Verification on 2026-09-12:

- Full backend suite with isolated stores: **251 passed, zero skipped**, 812.82s.
- Four HTTP cases verify mandatory retrieval, conflicting free-text scope ignored,
  missing/date-unresolved evidence refused without model calls, and one-sided
  drafts rejected. Two actual SDK cases verify server evidence serialization,
  no alternate tools, private metadata isolation and bilateral citation checks.
- Frontend: **15 passed**; generated OpenAPI/TypeScript types and production build
  passed. Changed assistant/provider/comparison-test Pyright: zero errors.
- Only backend/frontend containers rebuilt and restarted; no data publication,
  approval or ingestion ran. Live browser comparison correctly refused because
  reviewed NLS scoring evidence is unavailable in the current Publication.
- Desktop 1440px and mobile 390px screenshots inspected; 320px inputs fit;
  no horizontal overflow at any checked width. Existing user tabs were preserved.

Final two-axis review of the explicit-mode follow-up (`a1d2e1d`, original baseline
`4f87d77`): Standards found zero hard violations and the two unchanged low
maintainability advisories. Spec found zero new confirmed defects and confirmed
the prior P1 optional-routing blocker closed for explicit mode. Free-form Chat's
model-trust boundary is unchanged. Additional nonempty-history regression
coverage was suggested as a nonblocking improvement; explicit requests currently
discard prior history in both the service and provider.

The code path is implemented and runnable at http://localhost:5173/. Issue #12
remains open for review of the 14 pending real translations and separate exact
candidate/publication approvals. Successful real-data comparison and live model
evaluation remain gated by that evidence review; synthetic integration success
does not replace it.

## Published Evidence And Live Follow-up, 2026-09-14

Chris approved all 14 translations, then separately confirmed the exact candidate
and publication proposals. Decision `fb83f34b-2b7a-4b4a-a9c6-5b60505d8a48`
published version `5106927820d7b8d6a710009b5ff15b532df54314dd1ad391b0577a1638a72ae3`
at 06:31:53 UTC. The receipt and live API agree on that version; 50 Meetings
remain available. Private operational records are not implementation changes.

The first real comparison failed the governing-citation guard. A direct live
provider probe confirmed available evidence with 16 governing citations, but the
response schema allowed only 12. The generated structured list contained the
invalid ID `citation-12 classical` while the answer text referenced more passages.
The bounded capacity is now 32, with explicit exact-ID serialization instructions.
No fabricated citations are repaired or attached, and the bilateral guard remains
unchanged. A subsequent live answer was derived with all 16 valid FIA/VLN citations
and the unchanged publication version. This verifies the observed case, not a
guarantee of arbitrary model prose accuracy.

Explicit comparison freshness previously inherited all schedule-source attempts,
including unrelated GT World Challenge checks. It now uses the oldest verified
regulation document retrieval per Competition with separately declared F1/NLS
regulation policies, each conservatively retaining a 24-hour threshold. Missing
evidence remains unverified. F1's older document verification can legitimately
remain stale; no timestamp, source content or approved publication was changed.
Ordinary Chat and schedule freshness remain unchanged.

Validation:

- Full backend suite: **260 passed, zero skipped**, 945.45s, before the final
  explicit policy/model-validation refinement.
- After those refinements: **22 focused tests passed**, including seven freshness
  cases and SDK coverage for 16 citations, malformed/one-sided rejection and
  nonempty-history isolation. Existing dependency warnings remain.
- Final changed-file Pyright: zero errors. Final live HTTP checks after rebuilding
  only the backend: scoring derived with 16 bilateral citations; tyres and dated
  scoring unsupported with no citations; all three used the approved publication.
  Freshness correctly reported F1's 2026-09-10 17:50 UTC document check as expired
  and NLS's 2026-09-14 06:15 UTC check as current, without unrelated schedule checks.
  All 50 Meetings remained available; temporary session deletion returned 204.
- Two-axis follow-up review: Spec found no confirmed defects. Standards identified
  inherited universal expiry; corrected to explicit per-source regulation policy
  with an independence test. One low aggregation-duplication advisory remains.
- Successful live comparison evidence does not refresh schedule checks or extend
  historical applicability. Issue closure, push and merge have not been performed.