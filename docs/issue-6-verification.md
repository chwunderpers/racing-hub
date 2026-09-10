# Issue 6 Verification

Implementation for [Issue 6](https://github.com/chwunderpers/racing-hub/issues/6),
2026-09-10. Confirmed review baseline: `4226b07`. Confirmed test boundaries:
Adapter/fetch, review/publication/API, shared-Circuit SPARQL and browser interactions.

## Delivered

- Deterministic GT World Challenge Europe date-level Adapter: 12 Meetings,
  ten championship Rounds and two unnumbered prologues.
- Explicit versioned Circuit crosswalk. Spa, Monza, Barcelona and Zandvoort reuse
  F1 identities without label joins. New GT mappings require human resolutions.
- Coherent multi-season snapshots preserve the existing F1 season. Publication
  remains conditional on exact operational/RDF agreement and separate human gates.
- Field assertions retain raw labels, competing classification descriptions,
  source locations, retrieval times and selection rules. Timetable observations
  are not fabricated Sessions; missing tables/rows fail acquisition and reduced
  published observation counts block review until corrected.
- Identity-based UI filters, unnumbered prologue markers, shared-Circuit Meeting
  links, expandable assertions and independent per-source freshness.

## Verification Results

- Live public GET extraction: **12 Meetings, 10 Rounds, 2 prologues, 104 timetable
  observations, 5 blank names**. No raw markup retained in fixtures by the Adapter.
  The research report separately discloses earlier tool-log retention.
- Full backend run: **83 passed, 1 failed** in 432 seconds. The single failure was
  the old exact Meeting-view expectation omitting the new canonical ID fields.
  Updated that contract assertion; subsequent publication file: **6 passed**.
- After Standards/Spec review fixes, complete GT test file: **19 passed**, including
  isolated PostgreSQL/GraphDB publication, API, source-freshness and exact-version
  shared-Circuit SPARQL. The full suite was not rerun after these focused fixes.
- RDFLib/pyparsing emitted dependency deprecation warnings; no test errors remain
  in the focused checks. No unrelated dependency upgrade performed.
- Frontend: **9 tests passed**, TypeScript check passed, production build passed.
  OpenAPI and generated client types regenerated. Editor diagnostics clear.
- Browser: production build checked at 1440x1000, 390x844 and 320x780. Temporary
  browser-only responses added representative GT Spa Meetings to the live F1
  response; no data promotion occurred. Verified shared Circuit filtering across
  differing labels, prologue without a number, source disclosure, cross-Competition
  detail navigation and preserved filters. Screenshots inspected, no horizontal
  overflow or clipped detail text. Override removed; live 23-Meeting view restored.
- Rebuilt only backend/frontend containers with `--no-deps`; no bootstrap, volume
  reset or repository recreation. Application: <http://localhost:5173>.

## Standards

Parallel review of staged work against `4226b07` found two documented-standard
issues: optional assertion data controlled the GT mapping-resolution gate, and
missing timetable selectors passed silently. Both reproduced with failing tests
and were corrected. Mapping checks now depend on GT Competition scope; tables and
rows are required. Added review protection for reduced timetable observation counts.
No other consequential smell findings were reported.

## Spec

Independent parallel Spec review identified the same two issues; both are fixed
and covered by the final 19-test GT run. No scope creep was identified. Date-level
GT coverage is intentional: stable Session identities, end times and unambiguous
UTC-date conversion remain unverified. No invented values were introduced.

## Human Publication Gate

Live acquisition queued Review Item **`12e94701-d4b1-4bb5-8795-46c89952bb24`**.
Its combined candidate retains all 23 F1 Meetings/115 Sessions and adds 12 GT
Meetings. Preview: 12 additions, 12 explicit Circuit mapping resolutions, no
validation errors or publication conflicts. The full candidate and provenance
are retained in [the private review queue](../reviews/queue.yaml).

The live approved publication remains:

`5ceaf34cc28a433b064dd26a766647d36a3d6e0708fc96469adb7d81b1109590`

Its parsed candidate still hashes to that exact value, and the rebuilt API still
serves 23 Meetings with canonical identities. F1 freshness remains independently
verified; GT is marked pending review. No GT decision or publication was approved,
and no GT publication receipt exists. Acceptance criterion 1 remains incomplete
until the human accepts the exact candidate/mappings and separately confirms its
publication. Issue 6 must remain open until that receipt and live verification exist.

Use [the private review procedure](review-workflow.md) for the next step. The
implementation authorization is not a substitute for either data-publication gate.