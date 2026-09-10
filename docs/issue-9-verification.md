# Issue 9: Native GraphDB Semantic Assistant

## Scope And Environment

- Branch: `feature/9-graphdb-assistant`; review baseline: `769b56a`.
- Separate local GraphDB 11.5.0, native Streamable HTTP endpoint `/mcp`.
- Native server: GraphDB MCP Server 2.0.0, negotiated protocol `2025-03-26`.
- SDK: `mcp==1.24.0`; existing Agent Framework/Azure deployment unchanged.
- No hosting, source ingestion, new publication or inferred-data migration.

## Verification Evidence

Live checks on 2026-09-10:

- Native SELECT, ASK, CONSTRUCT and DESCRIBE all worked. ASK is a JSON boolean;
  native SELECT returns a JSON-encoded TSV string; graph forms return a
  JSON-encoded Turtle string. The client uses structured RDFLib parsers.
- Disposable-repository tests put conflicting labels for the same IRI in the
  current and historical graphs. All four native forms stayed within the current
  graph. Private `evidence` content did not reach the returned graph result.
- Authenticated assistant MCP reads succeeded. Anonymous repository query: 401;
  assistant SPARQL write: 403; assistant user administration: 403.
- Applied and reread server settings: query timeout 10 seconds, result ceiling
  1,000, hard timeout error enabled. Maintenance exact RDF agreement still passed
  for all 6,592 asserted triples; statement export is not truncated by the SPARQL
  result ceiling.
- Accepted Publication remained
  `df5eb36a8bff2a30bfd9d258f0599357c9bd84abab95d5c50163ea7aaa6d0af5`.
- Live website API plus the approved Azure deployment answered the shared-circuit
  acceptance question in 22.2 seconds (HTTP 200). It returned Barcelona-Catalunya
  (`f1-circuit-15`), Monza (`f1-circuit-39`), Zandvoort (`f1-circuit-55`) and Spa
  (`f1-circuit-7`), each shared by Formula One and GT World Challenge Europe.
  The answer carried eight real source citations, canonical Circuit and Competition
  IRIs, the unchanged publication version and classification `derived`.
- The live answer explicitly distinguished derived joins of asserted facts from
  OWL inference, and did not equate shared Circuits with identical Layouts or
  complete season coverage. NLS identities were not merged by display label.
- Actual MCP SDK tests verify separate sessions per tab, cancellation/DELETE on
  reset, native errors, malformed/oversized responses, compression rejection and
  stalled calls failing within the client deadline.
- Actual provider SDK transport tests verify the five backend-owned tools,
  server-resolved citations, no native tool-list forwarding, no credentials in
  model payloads and `store=false`.

## Deliberate Limits

Global GraphDB inferred facts are not exposed: the global default graph can mix
historical and unpublished premises. The assistant identifies asserted inputs and
derived results and explains why inferred-fact retrieval is unavailable. This is
not a new OWL inference facility.

The application still uses one backend worker and ephemeral browser capabilities.
Citation validation proves retrieval, not complete entailment of arbitrary model
prose. The historical generic assistant 503 cause was not recovered by this work.

## Final Gates

- Full backend suite: **161 passed in 382.96 seconds**, including authenticated
  disposable PostgreSQL/GraphDB fixtures; no skips.
- Frontend suite: **14 passed**, two files. TypeScript checking and Vite production
  build passed. Editor diagnostics reported no errors in the changed Python files.
- A fresh browser tab repeated the live semantic question with all four matches
  and eight citations. Desktop/mobile checks at 1440, 390 and 320 pixels found no
  page, answer or citation horizontal overflow. Desktop and mobile screenshots
  were inspected; localStorage and sessionStorage remained empty. No UI changes.
- The first full run was interrupted after 18 tests because PostgreSQL connections
  using `localhost` stalled on this Windows host. A narrow stack dump located the
  wait in psycopg connection establishment. The same permission test passed in
  16.65 seconds with `127.0.0.1`; the complete rerun above used literal IPv4 service
  addresses. Interrupted runs are not counted as successful full-suite runs.

## Standards

Independent review of `git diff 769b56a...e739be9` found no documented-standard
violations and three low-severity judgment concerns:

1. Reusing the MCP client after its exit stack closes might lack coverage.
   Disposition: the existing real-service isolation test runs all four forms
   sequentially through one client and passed in the full suite. AsyncExitStack
   accepts new contexts after `aclose()`; no lifecycle defect was reproduced.
2. The client manages per-query cleanup internally instead of requiring callers
   to own an async context. Disposition: intentional and documented; enter/exit
   must run in the tool's owning task. Cancellation and separate-tab tests pass.
3. Graph result dictionaries couple the transport result shape to citation
   extraction. Disposition: retained as a low-severity maintainability limitation;
   structured RDFLib output and the actual provider/MCP contract test cover the
   current shape. No additional abstraction was needed for this change.

## Spec

The independent Spec reviewer reported **no missing requirements, scope creep or
incorrect implementation** against Issue #9's six criteria, including the explicit
inference limitation documented above.

Review totals: Standards three low-severity judgment concerns, zero hard
violations; Spec zero findings. No blocking finding remains.