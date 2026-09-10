# Issue 5 Verification

Baseline: `22efac94b6871e7f79836ba6d42871afe0d00f4e`. Implementation committed on
the user-approved current `main` branch; no push or live publication is implied.

## Delivery

- Live ordinary-GET acquisition on 2026-09-10 queued 23 numbered Meetings as
  Review Item `c3384e4e-8dad-4e6d-93d9-407050597e63`; captured fixture has 115 Sessions.
- Adapter, season review, versioned PostgreSQL/GraphDB projection, source freshness
  and read-only API are implemented. The private Racing Source agent hands off
  to Racing Review for the existing separate exact-decision and publication gates.
- Competition/Circuit/date filters and shareable detail URLs preserve query state.
  Browser-local, event-local, UTC and selected IANA displays preserve resolved
  instants; unresolved clocks remain explicitly unconverted.
- Original public version remains
  `28c1e67d2560767a65df33e9689d46daed3fa744c49f680ceca6b255c4c5ba32`.
  The browser visibly marks it stale while the newer source candidate awaits review.

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
- Final app containers healthy at <http://localhost:5173>; public version unchanged.

## Remaining Gate

The source scope is the current F1 numbered calendar, not reconstructed historical
cancellation coverage. Factual PoC authorization is not legal clearance. See
[source workflow](source-workflow.md) for the approved-inventory checks and limits.
Human candidate acceptance and separate publication approval are still required.
The issue remains open for that operational handoff; implementation commits are local.