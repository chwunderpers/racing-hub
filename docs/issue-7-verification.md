# Issue 7 Verification

Baseline: `21a160f38db865425c95a2349a9c30a47cc3baeb`, explicitly confirmed by
Chris on 2026-09-10. Implementation checkpoint: `3263ac0`; subsequent review
fixes and publication receipts are included in the follow-up commit.

## Live Publication

Published at `2026-09-10T11:30:45.588079+00:00`:

`df5eb36a8bff2a30bfd9d258f0599357c9bd84abab95d5c50163ea7aaa6d0af5`

- 50 Meetings total: 23 F1, 12 GT, 15 NLS.
- NLS: eight championship Meetings with ten numbered Rounds, plus seven
  independent unnumbered test Meetings. April and September are double-headers.
- 146 Sessions total: 115 F1 and 31 NLS. NLS has 21 planned championship track
  periods and ten test windows. GT timetable observations remain noncanonical.
- NLS1 cancelled, NLS4 race abandoned; retained planned times and sourced status
  evidence. NLS2 date revision preserves its identity. No invented replacement.
- NLS7 nominal duration 360 minutes; ordinary races 240. Unknown Qualifiers end
  clocks remain null, and all NLS UTC instants remain unresolved.
- Explicit Venue and Layout: Qualifiers 25.378 km, ordinary 2026 length unknown;
  generic 24.358 km venue prose retained as scoped evidence only. Sprint-course
  test windows have distinct Session course references. No GT/NLS label merge.
- NLS Coverage State is incomplete, independently of successful source freshness.
  API and UI distinguish explicit empty, incomplete and unassessed scopes.

Live `/api/schedule` returned 50 Meetings, all ten NLS Round numbers, 146 Sessions,
NLS coverage `incomplete`, and aggregate `stale: false`. The post-publication
NLS fetch returned `unchanged`. Exact asserted GraphDB/publication agreement
passed against the promoted version. The prior F1/GT publication
`6effd015b1502e70ddf8f1b2f9d237d2fb8fd477672282d0c83f98f5e5c205d1`
remains readable and recomputes to exactly the same hash.

## Authorization And Evidence

- Standing authorization: [request](../reviews/requests/issue-7-standing-approval.json).
- Review Item: `98349cca-dee6-4066-94b3-82ebfb9465ed`.
- Decision: [9334b20e-6552-4cc0-a9e7-0834954b6ca7](../reviews/decisions/9334b20e-6552-4cc0-a9e7-0834954b6ca7.yaml).
- Publication receipt: [9334b20e-6552-4cc0-a9e7-0834954b6ca7](../reviews/publications/9334b20e-6552-4cc0-a9e7-0834954b6ca7.yaml).
- Decision confirmation: `4bd9421658532ada946b9bddf33994769bc3ed9841070cca3cec07747a9a593e`.
- Publication confirmation: `e432c236c30ef0f833e67a21569cd5627699d172e1109e9adaa7450b52cc5d80`.

The decision identifies Chris's standing authorization and agent-delegated
execution, not individual human review of every source. New NLS Circuit mappings
were explicitly resolved. Digest, stale-baseline, missing-record and exact RDF
agreement controls remain active. The queue item was removed after publication.
Source inventory, English factual translations, rights and incomplete evidence
are documented in [NLS research](sources/nls.md).

## Checks

- Full backend suite: **106 passed**, including isolated PostgreSQL/GraphDB
  integrations. 579 existing RDFLib/pyparsing dependency deprecation warnings.
- After review fixes: **22 NLS tests passed**, including real-store combined
  publication, version-pinned historical reads, Round-loss protection, parser
  failure handling, explicit coverage, and inherited/overridden Session Layouts.
- Frontend: **13 tests passed** after all review fixes, including the three
  strengthened published empty-state tests. Final production build and TypeScript
  typecheck passed, with all four Barlow font weights in the bundle.
- Live public source fetch: 15 Meetings, ten Rounds, 31 track periods and 82
  sourced assertions. No raw pages/PDFs retained and no blocked resource bypass.
- Live browser: desktop 1440x1000, mobile 390x844 and 320x844. Qualifiers details
  show both Rounds, abandonment, five Sessions, three unknown ends and incomplete
  coverage. DOM checks found no horizontal overflow/clipped detail controls.
  Desktop and 320px screenshots inspected; existing Barlow and palette preserved.
  Back-navigation retained the NLS filter and showed all 15 Meetings; font loading
  and absence of list overflow were also checked in the live browser.

## Review

### Standards

No hard documented-standard violations. The concrete duplicated Layout projection
gap was corrected with a shared helper and independent triple assertions. A
low-severity repeated grouping-conditional maintainability suggestion remains;
it is not a correctness blocker. Follow-up review confirmed the fix.

### Spec

Four findings corrected and confirmed in follow-up: revalidate cited calendar
route evidence; retain explicit unassessed coverage in RDF; preserve inherited
Session Layouts and lengths; remove contradictory first-publication wording for
published empty scopes. No remaining concrete finding in those reviewed areas.

## GraphDB Follow-up

The license gate described below was subsequently resolved using Chris's supplied
local license. GraphDB 11.5.0 is now live, with exact stored-graph preservation,
native MCP queries and 34 storage/NLS tests verified. Temporary copies were deleted.
See the [completed migration record](graphdb-upgrade.md) for final results and the
pre-existing oldest-seed regeneration limitation. The following records the
initial NLS closeout state, before the license was supplied.

The user also requested the GraphDB upgrade under this issue. The consistent-copy
migration rehearsal preserved `motorsport` and completed native MCP initialization
on 11.5.0, but data queries failed because no vendor-issued license was installed.
The original 10.8.10 service remains operational. The temporary migrated copy and
container were deleted, as requested. No backup archive remains.

The six original NLS criteria are implemented and verified. The added GraphDB
cutover remains incomplete until a valid 11.5 license is provided outside the
repository. See [migration record and prepared overlay](graphdb-upgrade.md).
No further ingestion approval is required for the local PoC.