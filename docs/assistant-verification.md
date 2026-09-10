# Issue 8 Verification

Implementation branch: `feature/8-schedule-assistant`.
Agreed review baseline: `59b4823` (after PR #20).
Verification date: 2026-09-10.

## Automated Checks

- Complete backend suite: **129 passed**, 630.44 seconds. Existing RDFLib /
  Pyparsing deprecation warnings remain (579 warnings).
- Complete frontend suite: **14 passed** in two files.
- Following review fixes: **21 passed** across documentation, assistant and
  restricted-principal tests. This includes two new NLS privacy/provenance tests.
- Frontend TypeScript check and production build passed with regenerated OpenAPI
  types. No reported diagnostics in the touched assistant modules.
- Actual PostgreSQL/GraphDB fixtures verify deterministic search publication,
  old-version visibility after injected search corruption, successful retry, and
  agreement through the graph, search, operational and assistant read boundaries.
- An actual temporary PostgreSQL login can read assistant views but cannot read
  raw envelopes/provenance, delete documents or create tables.
- An offline Responses HTTP transport exercises Microsoft Agent Framework tool
  invocation with dictionary arguments, structured answers, `store=false`, no
  provider conversation identifier, and the exact three-tool allowlist.
- Session checks cover separate histories, expiry, reset, active cancellation,
  concurrent-turn rejection, typed input limits, unknown citations and refusal
  without current-turn retrieved evidence.

## Local Acceptance

The approved Azure deployment answered actual browser questions:

1. Australian Grand Prix: March 6-8; race at 05:00 Europe/Berlin on March 8;
   official Formula One source and retrieval timestamp; differing Meeting and
   Session statuses preserved; answer classified as derived.
2. NLS Qualifiers Round 4: abandoned after starting, with incomplete coverage;
   citation resolves to the April 18 race-control bulletin, not the preview.
3. Albert Park: canonical `Circuit` type and stable resource IRI, retrieved from
   published documentation and linked to the official Formula One source.

Desktop (1440 pixels) and mobile (390 pixels) screenshots were inspected. The
320-pixel viewport had no horizontal overflow. Reset and reload cleared the
transcript; a new tab started empty. Neither localStorage nor sessionStorage
contained chat state. Backend isolation is additionally checked independently of
the UI. These are bounded acceptance checks, not an exhaustive evaluation of
model entailment or adversarial prompt injection.

Backend and frontend were rebuilt and started locally. The sanitized search
projection was backfilled and the reader login refreshed. The live publication
remains `df5eb36a8bff2a30bfd9d258f0599357c9bd84abab95d5c50163ea7aaa6d0af5`;
no source acquisition or new publication was performed for this feature.

## Standards Review

The independent Standards review found one documented testing gap and two
heuristic concerns:

- Search-failure coverage originally tested the promotion guard directly. It now
  injects missing search documents through `PublicationModule.publish()` and
  verifies all read representations before and after retry.
- Assistant freshness was an untyped dictionary. It now reuses the schedule's
  typed freshness response, including generated frontend types.
- Coverage defaults are duplicated between the restricted reader and existing
  publication view. This low-severity heuristic remains; consolidating it is not
  necessary for the accepted behavior and would widen this security repair.

## Spec Review

The independent Spec review found two defects, both fixed with regressions:

- NLS envelope evidence included private authorization notes. The public Markdown
  projection now excludes that maintenance narrative, in addition to dedicated
  reviewer/authorization fields. The real NLS projection and restricted reader
  are checked for absence of those notes.
- Schedule facts previously shared one Meeting source. Sanitized field-level
  assertions now carry their actual source citations and preserve alternatives.
  Both PostgreSQL integration and a live answer verify the race-control source.

No concrete scope creep was found. Native GraphDB MCP assistant integration
remains Issue #9. Citation validation checks retrieved source identities, not
semantic entailment of every natural-language claim. Provider service retention
policies are separate from the application's ephemeral session behavior.