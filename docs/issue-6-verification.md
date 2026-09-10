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

## Approved Publication

Live acquisition queued Review Item **`12e94701-d4b1-4bb5-8795-46c89952bb24`**.
Chris explicitly accepted its candidate and all 12 Circuit mappings, confirmed the
exact decision, then separately approved publication of the exact proposed version.
The combined candidate retains all 23 F1 Meetings/115 Sessions and adds 12 GT
Meetings. Preview: 12 additions, no validation errors or publication conflicts.
The full candidate and provenance are retained in the immutable
[decision record](../reviews/decisions/f53248fa-d06f-4882-b473-078fc9fb3cad.yaml).

Decision **`f53248fa-d06f-4882-b473-078fc9fb3cad`** was recorded at
`2026-09-10T10:27:54.811595+00:00`. Publication succeeded at
`2026-09-10T10:28:44.846353+00:00`; see the
[publication receipt](../reviews/publications/f53248fa-d06f-4882-b473-078fc9fb3cad.yaml).

The live approved publication is:

`6effd015b1502e70ddf8f1b2f9d237d2fb8fd477672282d0c83f98f5e5c205d1`

It supersedes F1-only baseline
`5ceaf34cc28a433b064dd26a766647d36a3d6e0708fc96469adb7d81b1109590`
without changing the retained F1 season. A post-publication GT fetch returned
`unchanged` and cleared the pending-review freshness marker.

Live verification passed: API returns 35 Meetings, 12 GT Meetings, ten GT Rounds,
two prologues with null Round number/identity, and 115 F1 Sessions under the exact
published version. Freshness reports `stale: false`. SPARQL against that version's
named graph returns the four shared Circuit identities `f1-circuit-7`,
`f1-circuit-15`, `f1-circuit-39` and `f1-circuit-55`.

Browser verification used the actual live API without overrides: all 12 GT Meetings
visible under the Competition filter; Spa Prologue links to the GT Spa Meeting and
F1 Belgian Grand Prix, displays 14 source assertions and the exact published version.
No stale notice remains. All six Issue 6 acceptance criteria are now satisfied for
the local date-level PoC. Future changes still require the
[private review procedure](review-workflow.md) and separate publication approval.