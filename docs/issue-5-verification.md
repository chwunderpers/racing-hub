# Issue 5 Verification

Baseline: `22efac94b6871e7f79836ba6d42871afe0d00f4e`. Implementation committed on
the user-approved current `main` branch. Chris subsequently confirmed the exact
acceptance proposal and separately approved publication, then authorized Issue 5
closeout including pushing the scoped work and closing the ticket.

## Delivery

- Live ordinary-GET acquisition on 2026-09-10 queued 23 numbered Meetings as
  Review Item `c3384e4e-8dad-4e6d-93d9-407050597e63`; captured fixture has 115 Sessions.
- Adapter, season review, versioned PostgreSQL/GraphDB projection, source freshness
  and read-only API are implemented. The private Racing Source agent hands off
  to Racing Review for the existing separate exact-decision and publication gates.
- Competition/Circuit/date filters and shareable detail URLs preserve query state.
  Browser-local, event-local, UTC and selected IANA displays preserve resolved
  instants; unresolved clocks remain explicitly unconverted.
- Published version is
  `5ceaf34cc28a433b064dd26a766647d36a3d6e0708fc96469adb7d81b1109590`, replacing
  the original Australia-only version after both explicit human approvals.
  Decision: `01a282eb-adf0-431d-b98f-181143c59b82`, person Chris, rationale
  "looking good, no blockers", evidence `https://www.formula1.com/en/racing/2026`.
  [Publication receipt](../reviews/publications/01a282eb-adf0-431d-b98f-181143c59b82.yaml)
  records success at 2026-09-10 09:33:16 UTC. The pending queue is empty.

## Standards

Parallel review reported one P2 consistency issue and one P3 judgment:

- **Fixed:** host timezone rules could change projections during retry. Clock
  assertions now hash their rules version and resolve only from the pinned packaged
  tzdata 2026.3. A mismatched installed version blocks resolution.
- **Retained judgment:** per-Meeting preview comparison is duplicated between
  legacy single-Meeting and season review paths. A shared comparison helper is a
  possible future refactor, not a documented-standard violation or delivery blocker.

## Spec

Parallel review reported four findings, all fixed with focused regressions:

- **P1:** signed Flight text lengths could create a nonadvancing parsing loop.
  Unsigned hexadecimal validation and existing bounds now guarantee forward progress.
- **P2:** partial Session lists could pass coverage validation. The Adapter now
  checks verified regular/Sprint code sets; review blocks missing published Sessions.
- **P2:** malformed Session objects could bypass stale marking. Payload shape
  validation now routes these failures through recorded source-failure handling.
- **P2:** invalid URL dates could invisibly filter records. Strict calendar-date
  validation now displays an alert and excludes malformed values from filtering.

## Checks

- Full backend suite: 64 passed before review follow-ups.
- Final focused season/Adapter/fetch/review suite: 19 passed plus the real-store
  parametrization separately passed (20 total), including five new review regressions.
- Frontend suite: 8 passed after review fixes; final Docker production build and
  typecheck succeeded. Editor diagnostics clear.
- Browser checks at 390/768/1440 widths: no horizontal page overflow or overflowing
  session-text containers. UTC and America/New_York clocks verified, unresolved date
  retained, and Back-to-schedule/browser Back preserved the Circuit filter.
  Session presentation used browser-only test data; no test data was published.
- Final app containers healthy at <http://localhost:5173>.
- Post-publication source fetch at 2026-09-10 09:36:19 UTC returned `unchanged`
  for the approved version. The documented reconciliation cleared the previous
  pending-revision marker without another candidate, approval or publication.
  Live API assertions passed: 23 Meetings, 115 Sessions, exactly the approved
  publication version, `freshness.stale: false`, and no stale reason.

## Closeout

The source scope is the current F1 numbered calendar, not reconstructed historical
cancellation coverage. Factual PoC authorization is not legal clearance. See
[source workflow](source-workflow.md) for the approved-inventory checks and limits.
This candidate's human acceptance and publication gates are complete. Future data
revisions retain those gates; routine implementation and closeout actions do not
require repeated operator decisions. No runtime code change was needed to reconcile
freshness. The decision, request and publication receipt are retained with the work.